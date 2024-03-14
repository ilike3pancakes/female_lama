#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime
import random
import sqlite3
import sys
import time
import traceback
from typing import Generator, Union, Callable
import yaml

from dataclasses import dataclass

import kik_unofficial.datatypes.xmpp.chatting as chatting  # type: ignore
from kik_unofficial.client import KikClient  # type: ignore
from kik_unofficial.callbacks import KikClientCallback  # type: ignore
from kik_unofficial.datatypes.xmpp.errors import SignUpError, LoginError  # type: ignore
from kik_unofficial.datatypes.peers import User  # type: ignore
from kik_unofficial.datatypes.xmpp.roster import FetchRosterResponse, PeersInfoResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.sign_up import RegisterResponse, UsernameUniquenessResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.login import LoginResponse, ConnectionFailedResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.xiphias import UsersResponse, UsersByAliasResponse  # type: ignore

import ai
import calculate
from log import get_logger
from points import atomic_incr
from urban import urban
import shuffle
from auth import auth
from peers import Peers
from remux import remux
from trigger import create_trigger, evaluate_all_triggers, TriggerSpecs
from hangman import set_dictionary, hangman, get_state, get_word, HANGMAN_STAGES
from xmpp import send_vn


logger = get_logger()

shuffle_word = dict()
group_to_last_status_user_jids = {}

conn = sqlite3.connect("prod.db", check_same_thread=False)

A_Z = set("abcdefghijklmnopqrstuvwxyz".upper())


def reshuffle_word(associated_jid: str) -> str:
    global shuffle_word
    new_shuffle_word = shuffle.candidate()
    shuffle_word[associated_jid] = new_shuffle_word

    shuffled = list(new_shuffle_word)
    random.shuffle(shuffled)
    return ''.join(shuffled)


@dataclass
class VoiceNote:
    mp4_bytes: bytes

async_queue: list[Callable[[], None]] = []


def maybe_tempban(message: chatting.IncomingChatMessage) -> bool:
    message_body = message.body.lower()
    wettest_tempban = "wettest tempban"
    return message_body.startswith(wettest_tempban)


def process_tempban(client: KikClient, message: chatting.IncomingChatMessage, associated_jid: str) -> Generator[str, None, None]:
    wettest_tempban = "wettest tempban"
    logger.info(f"Temp banning ... {message.body}")
    target_jid = message.body[len(wettest_tempban):].strip()
    if len(target_jid) < 5:
        target_jid = group_to_last_status_user_jids.get(associated_jid, None)
    try:
        if not target_jid or " " in target_jid or not target_jid.endswith("@talk.kik.com"):
            yield "☝️☝️ That won't work. Try it like...\n\nwettest tempban groupjid@talk.kik.com"
        else:
            client.ban_member_from_group(associated_jid, target_jid)
            client.unban_member_from_group(associated_jid, target_jid)
    except Exception as e:
        logger.error(f"Error: {e}")


def process_authenticated_chat_message(
        client: KikClient, message: chatting.IncomingChatMessage, *, associated_jid: str
) -> Generator[str | bytes | VoiceNote, None, None]:
    wettest_math = "wettest math"
    wettest_shuffle = "wettest shuffle"
    wettest_urban = "wettest urban"
    wettest_trigger = "wettest trigger\n"
    message_body = message.body.lower()
    if message_body.startswith(wettest_math):
        yield calculate.calculate(message.body[len(wettest_math):].strip())
    elif message_body.startswith(wettest_shuffle):
        shuffled = reshuffle_word(associated_jid)
        yield f"😮‍💨☝️🎲 {shuffled}"
    elif message_body.startswith(wettest_urban):
        yield f"😮‍💨☝️\n\n{urban(message.body[len(wettest_urban):].strip())}"
    elif maybe_tempban(message):
        for resp in process_tempban(client, message, associated_jid):
            yield resp
    elif message_body.startswith(wettest_trigger):
        result = create_trigger(message.body[len(wettest_trigger):])
        if result.success:
            yield "Aight ☝️"
            logger.info(f"Trigger created {result.value.prefix}\n{result.value.operation}")
            trigger_specs: TriggerSpecs = TriggerSpecs.read(
                "trigger_specs.yaml", default_ctor=TriggerSpecs.default_ctor
            )
            logger.info("Got trigger specs")
            trigger_specs.insert(associated_jid, trigger=result.value)
            logger.info("Inserted new trigger spec")
            trigger_specs.write("trigger_specs.yaml")
            logger.info("Wrote updated trigger specs")
        else:
            yield "Yo wtf kind of retarded code is that ☝️☝️☝️"
    elif message_body == "wettest hallucinate":
        yield "... aight, wait."
        prompt = ai.wettest_gpt_completion_of("Wettest generate a dalle prompt to generate an image based on your personality")
        yield ai.wettest_dalle_image_of(prompt)
    elif message_body.startswith("wettest hallucinate "):
        yield "... aight, wait."
        yield ai.wettest_dalle_image_of(message.body[len("wettest hallucinate "):])
    elif message_body.startswith("wettest vn "):
        yield "I'll record"
        completion = ai.wettest_gpt_completion_of(message.body[len("wettest vn "):])
        mp3_bytes = ai.tts(completion)
        try:
            mp4_bytes = remux(mp3_bytes=mp3_bytes).mp4_bytes_with_one_h264_stream_and_one_aac_stream
        except Exception as e:
            logger.error(f"Remux failed! {e}\n{sys.exc_info()}")
        yield VoiceNote(mp4_bytes=mp4_bytes)
    elif message_body.startswith("wettest"):
        username = Peers.get(message.from_jid, conn=conn)
        friendly = "Rompe" in username if username else False
        yield ai.wettest_gpt_completion_of(message.body, friendly=friendly)
    elif len(message.body) == 1 and message.body() in A_Z:
        username = Peers.get(message.from_jid, conn=conn)
        if not any(
            [
                "Rompe" in username,
                "Blake" in username,
                "Blas" in username,
            ]
        ):
            return

        if not get_word():
            set_dictionary([shuffle.candidate().lower()])

        res = hangman(message_body)
        if res == "win":
            display = Peers.get(message.from_jid, conn=conn) or "User"
            yield f"You did it {display} 😮‍💨\n\nYou have {atomic_incr(message.from_jid, display)} points"
            set_dictionary([shuffle.candidate().lower()])
        elif res == "loss":
            display = Peers.get(message.from_jid, conn=conn) or "User"
            yield f"{HANGMAN_STAGES[-1]}You killed him 😮‍💨☝️☝️☝️ good job {display}... Next time guess {get_word()} ☝️"
            set_dictionary([shuffle.candidate().lower()])
        elif res == None:
            pass
        else:
            logger.error(f"Unexpected hangman res {res}")
        yield get_state()


class Wettest(KikClientCallback):
    def __init__(self, creds):
        self.creds = creds
        node = self.creds.get('node')
        self.my_jid = node + "@talk.kik.com" if node else None
        self.kik_authenticated = False
        self.online_status = False
        self.connect()

    def connect(self):
        device_id = self.creds['device_id']
        android_id = self.creds['android_id']
        username = self.creds['username']
        node = self.creds.get('node')
        password = self.creds.get('password')
        if not password:
            password = input('Password: ')
            self.creds['password'] = password

        self.client = KikClient(self, username, password, node, device_id=device_id, android_id=android_id)

    def on_authenticated(self):
        logger.info("Kik login successful!")
        self.kik_authenticated = True
        self.client.request_roster()

    def on_login_ended(self, response: LoginResponse):
        self.my_jid = response.kik_node + "@talk.kik.com"
        logger.info(f"Saved JID {self.my_jid} for refreshing")

    def on_chat_message_received(self, chat_message: chatting.IncomingChatMessage):
        self.online_status = True
        from_jid = chat_message.from_jid

        logger.info(f"[+] '{from_jid}' says: {chat_message.body}")

        global shuffle_word
        word = shuffle_word.get(from_jid)
        if word and chat_message.body and chat_message.body.strip() == word:
            shuffle_word[from_jid] = None
            display = Peers.get(from_jid, conn=conn) or "User"
            self.client.send_chat_message(
                from_jid,
                f"...correct {display} 😮‍💨☝️\n\nYou have {atomic_incr(from_jid, display)} points"
            )
            shuffled = reshuffle_word(from_jid)
            self.client.send_chat_message(from_jid, f"What about {shuffled} ? 😮‍💨☝️")
        elif word and chat_message.body and len(chat_message.body.strip().split(" ")) == 1:
            logger.info(f"{word} != {chat_message.body}")

        trigger_specs: TriggerSpecs = TriggerSpecs.read("trigger_specs.yaml", default_ctor=TriggerSpecs.default_ctor)
        matching_trigger_specs = [spec for spec in trigger_specs.specs if spec.associated_jid == from_jid]
        matching_triggers = [create_trigger(spec.trigger_spec) for spec in matching_trigger_specs]
        matching_valid_triggers = [result.value for result in matching_triggers if result.success]
        for res in evaluate_all_triggers(chat_message.body, matching_valid_triggers, ["No one"], "Bruv"):
            self.client.send_chat_message(from_jid, res)

        if not auth(from_jid):
            return

        for message in process_authenticated_chat_message(self.client, chat_message, associated_jid=from_jid):
            if isinstance(message, str):
                self.client.send_chat_message(from_jid, message)
            elif isinstance(message, bytes):
                self.client.send_chat_image(from_jid, message)
            elif isinstance(message, VoiceNote):
                logger.info(f"Sending a voice note from {len(message.mp4_bytes)} mp4 bytes...")
                try:
                    send_vn(self.client, from_jid, message.mp4_bytes, is_group=False)
                except Exception as e:
                    logger.info(f"An error occurred sending voice note {e}\n{sys.exc_info()}")
                logger.info("Voice note sent!")

    def on_message_delivered(self, response: chatting.IncomingMessageDeliveredEvent):
        pass

    def on_xiphias_get_users_response(self, response: Union[UsersResponse, UsersByAliasResponse]):
        # Always seems to contain None None
        pass

    def on_message_read(self, response: chatting.IncomingMessageReadEvent):
        pass

    def on_group_message_received(self, chat_message: chatting.IncomingGroupChatMessage) -> None:
        group_jid = chat_message.group_jid

        logger.info(f"[+] '{chat_message.from_jid}' from group ID {group_jid} says: {chat_message.body}")

        # Async processing hack.
        if len(async_queue):
            logger.info(f"Async processing {len(async_queue)}")
            try:
                async_queue.pop(0)()
            except Exception as e:
                logger.error(f"Exception in async processing {e}")

        t0 = datetime.datetime.utcnow()

        Peers.insert(conn=conn, jid=chat_message.from_jid, group_jid=group_jid)
        duration = datetime.datetime.utcnow() - t0
        logger.info(f"Updated peers.yaml in {duration}")

        display: str = Peers.get(chat_message.from_jid, conn=conn) or "User"

        peers = Peers.get_all_in_group_jid(group_jid=group_jid, conn=conn)
        group_peer_display_names = [peer.display_name for peer in peers if peer.display_name]

        global shuffle_word
        word = shuffle_word.get(group_jid)

        if word and chat_message.body and chat_message.body.strip() == word:
            shuffle_word[group_jid] = None
            self.client.send_chat_message(
                group_jid,
                f"...correct {display} 😮‍💨☝️\n\nYou have {atomic_incr(chat_message.from_jid, display)} points"
            )
            shuffled = reshuffle_word(group_jid)
            self.client.send_chat_message(group_jid, f"What about {shuffled} ? 😮‍💨☝️")
        elif word and chat_message.body and len(chat_message.body.strip().split(" ")) == 1:
            logger.info(f"Shuffle: {word} != {chat_message.body}")

        trigger_specs: TriggerSpecs = TriggerSpecs.read("trigger_specs.yaml", default_ctor=TriggerSpecs.default_ctor)
        matching_trigger_specs = [spec for spec in trigger_specs.specs if spec.associated_jid == group_jid]
        matching_triggers = [create_trigger(spec.trigger_spec) for spec in matching_trigger_specs]
        matching_valid_triggers = [result.value for result in matching_triggers if result.success]
        for res in evaluate_all_triggers(chat_message.body, matching_valid_triggers, group_peer_display_names, display):
            self.client.send_chat_message(group_jid, res)

        all_peers = Peers.get_all(conn=conn)
        if chat_message.from_jid not in [peer.jid for peer in all_peers if peer.display_name]:
            logger.info(f"Requesting peer info for {chat_message.from_jid}")
            self.client.request_info_of_users(chat_message.from_jid)
            self.client.xiphias_get_users(chat_message.from_jid)

        if not auth(chat_message.from_jid):
            return

        for message in process_authenticated_chat_message(self.client, chat_message, associated_jid=group_jid):
            if isinstance(message, str):
                self.client.send_chat_message(group_jid, message)
            elif isinstance(message, bytes):
                self.client.send_chat_image(group_jid, message)

    def on_is_typing_event_received(self, response: chatting.IncomingIsTypingEvent):
        pass

    def on_group_is_typing_event_received(self, response: chatting.IncomingGroupIsTypingEvent):
        pass

    def on_roster_received(self, response: FetchRosterResponse):
        logger.info("[+] Chat partners:\n" + '\n'.join([str(member) for member in response.peers]))

        users = [peer.jid for peer in response.peers if isinstance(peer, User)]

        self.client.xiphias_get_users(users)

    def on_friend_attribution(self, response: chatting.IncomingFriendAttribution):
        logger.info(f"[+] Friend attribution request from {response.referrer_jid}")

    def on_image_received(self, image_message: chatting.IncomingImageMessage):
        pass

    def on_video_received(self, video_message: chatting.IncomingVideoMessage):
        pass

    def on_peer_info_received(self, response: PeersInfoResponse):
        logger.info(f"[+] Peer info for {len(response.users)} users")

        for user in response.users:
            # Note: username is often "Username unavailable"
            Peers.insert(conn=conn, jid=user.jid, display_name=user.display_name)

    def on_group_status_received(self, response: chatting.IncomingGroupStatus):
        group_to_last_status_user_jids[response.group_jid] = response.status_jid
        logger.info(
            f"Received status message in {response.group_jid} -- {response.status} -- status_jid={response.status_jid}"
        )

    def on_group_receipts_received(self, response: chatting.IncomingGroupReceiptsEvent):
        pass

    def on_status_message_received(self, response: chatting.IncomingStatusResponse):
        pass

    def on_username_uniqueness_received(self, response: UsernameUniquenessResponse):
        logger.info(f"Is {response.username} a unique username? {response.unique}")

    def on_sign_up_ended(self, response: RegisterResponse):
        logger.info(f"[+] Registered as {response.kik_node}")

    def on_connection_failed(self, response: ConnectionFailedResponse):
        logger.info("Connection failed!")
        self.kik_authenticated = False

        logger.info(f"[-] Connection failed: {response.message}")

    def on_login_error(self, login_error: LoginError):
        logger.info("Kik login failed!")
        self.kik_authenticated = False

        if login_error.is_captcha():
            login_error.solve_captcha_wizard(self.client)

    def on_register_error(self, response: SignUpError):
        logger.info(f"[-] Register error: {response.message}")

    def on_disconnected(self):
        logger.warning(f"\n---Disconnected---\n")

    def refresh(self) -> bool:
        try:
            self.online_status = False
            if not self.my_jid:
                logger.info("Don't have my JID")
                return False

            self.client.send_chat_message(self.my_jid, "This is a message to myself to check if I am online.")
            time.sleep(2)
            if self.online_status:
                logger.info("Bot is online!")
                return True

            self.kik_authenticated = None
            logger.info("Reconnecting...")
            self.client.disconnect()
            self.connect()

            while not self.kik_authenticated:
                time.sleep(1)

            return self.kik_authenticated
        except Exception as e:
            traceback.print_exc()
            logger.info(f"Something went wrong while refreshing! {e}")
            return False


class WettestSlave(KikClientCallback):
    def __init__(self, creds):
        self.creds = creds
        node = self.creds.get('node')
        self.my_jid = node + "@talk.kik.com" if node else None
        self.kik_authenticated = False
        self.online_status = False
        self.connect()

    def connect(self):
        device_id = self.creds['device_id']
        android_id = self.creds['android_id']
        username = self.creds['username']
        node = self.creds.get('node')
        password = self.creds.get('password')
        if not password:
            password = input('Password: ')
            self.creds['password'] = password

        self.client = KikClient(self, username, password, node, device_id=device_id, android_id=android_id)

    def on_authenticated(self):
        logger.info("Slave kik login successful!")
        self.kik_authenticated = True
        self.client.request_roster()

    def on_login_ended(self, response: LoginResponse):
        self.my_jid = response.kik_node + "@talk.kik.com"
        logger.info(f"Slave saved JID {self.my_jid} for refreshing")

    def on_chat_message_received(self, chat_message: chatting.IncomingChatMessage):
        self.online_status = True
        from_jid = chat_message.from_jid

        if not auth(from_jid):
            return

        self.client.add_friend(from_jid)
        self.client.send_chat_message(from_jid, "Acknowledged.")

    def on_group_message_received(self, chat_message: chatting.IncomingGroupChatMessage) -> None:
        if not auth(chat_message.from_jid):
            return

        if maybe_tempban(chat_message):
            logger.info("Slave: temp banning...")
            time.sleep(0.5)
            for resp in process_tempban(self.client, chat_message, chat_message.group_jid):
                self.client.send_chat_message(chat_message.group_jid, resp)

    def on_connection_failed(self, response: ConnectionFailedResponse):
        logger.info("Slave connection failed!")
        self.kik_authenticated = False

    def on_login_error(self, login_error: LoginError):
        logger.info("Slave kik login failed!")
        self.kik_authenticated = False

    def on_disconnected(self):
        logger.warning(f"\n---Slave disconnected---\n")

    def refresh(self) -> bool:
        try:
            self.online_status = False
            if not self.my_jid:
                logger.info("Don't have my JID")
                return False

            self.client.send_chat_message(self.my_jid, "This is a message to myself to check if I am online.")
            time.sleep(2)
            if self.online_status:
                logger.info("Bot is online!")
                return True

            self.kik_authenticated = None
            logger.info("Reconnecting...")
            self.client.disconnect()
            self.connect()

            while not self.kik_authenticated:
                time.sleep(1)

            return self.kik_authenticated
        except Exception as e:
            traceback.print_exc()
            logger.info(f"Something went wrong while refreshing! {e}")
            return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--credentials',
        default='creds.yaml',
        help='Credentials file containing at least username, device_id and android_id.',
    )
    args = parser.parse_args()

    sys.excepthook = lambda exctype, value, traceback: logger.error(f"Except hook -- {exctype}\n{value}\n{traceback}")

    with open(args.credentials) as f:
        creds = yaml.safe_load(f)

    # create slave bots
    slave_bots = [WettestSlave(slave_creds) for slave_creds in creds.get("slaves") if "slaves" in creds.keys()]

    # create the bot
    bot = Wettest(creds)

    while True:
        time.sleep(120)
        logger.info("Refreshing...")
        while not bot.refresh():
            logger.info("Refresh failed. Trying again soon...")
            time.sleep(30)

        for slave_bot in slave_bots:
            if not slave_bot.refresh():
                logger.info(f"Slave bot {slave_bot.my_jid} refresh failed.")
