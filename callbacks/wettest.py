from __future__ import annotations

from dataclasses import dataclass
import datetime
import random
from sqlite3 import Connection
import sys
import time
import traceback
import typing
from typing import Callable, Generator, Union

import kik_unofficial.datatypes.xmpp.chatting as chatting  # type: ignore
from kik_unofficial.callbacks import KikClientCallback  # type: ignore
from kik_unofficial.client import KikClient  # type: ignore
from kik_unofficial.datatypes.peers import User  # type: ignore
from kik_unofficial.datatypes.xmpp.errors import SignUpError, LoginError  # type: ignore
from kik_unofficial.datatypes.xmpp.login import LoginResponse, ConnectionFailedResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.roster import FetchRosterResponse, PeersInfoResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.sign_up import RegisterResponse, UsernameUniquenessResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.xiphias import UsersResponse, UsersByAliasResponse  # type: ignore

import ai
import calculate
from auth import auth
from callbacks.common.tempban import maybe_tempban, process_tempban, group_to_last_status_user_jids
from hangman import set_dictionary, hangman, get_state, get_word, HANGMAN_STAGES
from log import get_logger
from peers import Peers
from points import atomic_incr
from remux import remux
import shuffle
from trigger import create_trigger, evaluate_all_triggers, TriggerSpecs
from urban import urban
from xmpp import send_vn


shuffle_word = dict()

logger = get_logger()

A_Z = set("abcdefghijklmnopqrstuvwxyz".upper())

async_queue: list[Callable[[], None]] = []


@dataclass
class VoiceNote:
    mp4_bytes: bytes


def process_authenticated_chat_message(
        client: KikClient, message: chatting.IncomingChatMessage, *, associated_jid: str, conn: Connection,
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
            logger.info("Remux succeeded.")
        except Exception as e:
            logger.error(f"Remux failed! {e}\n{sys.exc_info()}")

        logger.info("Yielding voice note...")
        yield VoiceNote(mp4_bytes=mp4_bytes)
    elif message_body.startswith("wettest"):
        username = Peers.get(message.from_jid, conn=conn)
        friendly = "Rompe" in username if username else False
        yield ai.wettest_gpt_completion_of(message.body, friendly=friendly)
    elif len(message.body) == 1 and message.body in A_Z:
        username = Peers.get(message.from_jid, conn=conn)
        if not username or not any(
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


def reshuffle_word(associated_jid: str) -> str:
    global shuffle_word
    new_shuffle_word = shuffle.candidate()
    shuffle_word[associated_jid] = new_shuffle_word

    shuffled = list(new_shuffle_word)
    random.shuffle(shuffled)
    return ''.join(shuffled)


class Wettest(KikClientCallback):
    def __init__(self, *, creds: dict[str, typing.Any], sql: Connection):
        self.creds = creds
        self.sql = sql
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

        global shuffle_word
        word = shuffle_word.get(from_jid)
        if word and chat_message.body and chat_message.body.strip() == word:
            shuffle_word[from_jid] = None
            display = Peers.get(from_jid, conn=self.sql) or "User"
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

        try:
            for message in process_authenticated_chat_message(self.client, chat_message, associated_jid=from_jid, conn=self.sql):
                if isinstance(message, str):
                    self.client.send_chat_message(from_jid, message)
                elif isinstance(message, bytes):
                    self.client.send_chat_image(from_jid, message)
                elif isinstance(message, VoiceNote):
                    logger.info(f"Sending a voice note from {len(message.mp4_bytes)} mp4 bytes...")
                    send_vn(self.client, from_jid, message.mp4_bytes, is_group=False)
                    logger.info("Voice note sent!")
        except Exception as e:
            logger.error(f"Something went wrong processing authenticated messages... {e}", exc_info=1)

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

        Peers.insert(conn=self.sql, jid=chat_message.from_jid, group_jid=group_jid)
        duration = datetime.datetime.utcnow() - t0
        logger.info(f"Updated peers.yaml in {duration}")

        display: str = Peers.get(chat_message.from_jid, conn=self.sql) or "User"

        peers = Peers.get_all_in_group_jid(group_jid=group_jid, conn=self.sql)
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

        all_peers = Peers.get_all(conn=self.sql)
        if chat_message.from_jid not in [peer.jid for peer in all_peers if peer.display_name]:
            logger.info(f"Requesting peer info for {chat_message.from_jid}")
            self.client.request_info_of_users(chat_message.from_jid)
            self.client.xiphias_get_users(chat_message.from_jid)

        if not auth(chat_message.from_jid):
            return

        for message in process_authenticated_chat_message(self.client, chat_message, associated_jid=group_jid, conn=self.sql):
            if isinstance(message, str):
                self.client.send_chat_message(group_jid, message)
            elif isinstance(message, bytes):
                self.client.send_chat_image(group_jid, message)
            elif isinstance(message, VoiceNote):
                logger.info(f"Sending a voice note from {len(message.mp4_bytes)} mp4 bytes...")
                send_vn(self.client, group_jid, message.mp4_bytes, is_group=True)
                logger.info("Voice note sent!")

    def on_is_typing_event_received(self, response: chatting.IncomingIsTypingEvent):
        pass

    def on_group_is_typing_event_received(self, response: chatting.IncomingGroupIsTypingEvent):
        pass

    def on_roster_received(self, response: FetchRosterResponse):
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
            Peers.insert(conn=self.sql, jid=user.jid, display_name=user.display_name)

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
