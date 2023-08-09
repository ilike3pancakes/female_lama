#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import random
import sys
import time
import traceback
from typing import Generator, Union
import yaml

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
from points import atomic_incr
import shuffle
from auth import auth

shuffle_word = dict()
peers = dict()


def process_chat_message(message: chatting.IncomingChatMessage, *, associated_jid: str) -> Generator[str, None, None]:
    wettest_math = "wettest math"
    wettest_shuffle = "wettest shuffle"
    if message.body.lower().startswith(wettest_math):
        yield calculate.calculate(message.body[len(wettest_math):].strip())
    elif message.body.lower().startswith(wettest_shuffle):
        global shuffle_word
        new_shuffle_word = shuffle.candidate()
        shuffle_word[associated_jid] = new_shuffle_word

        shuffled = list(new_shuffle_word)
        random.shuffle(shuffled)
        yield f"😮‍💨☝️🎲 {''.join(shuffled)}"
    elif message.body.lower().startswith("wettest"):
        yield ai.wettest_gpt_completion_of(message.body)


class EchoBot(KikClientCallback):
    def __init__(self, creds):
        self.creds = creds
        self.my_jid = self.creds.get('node') + "@talk.kik.com"
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
        print("Kik login successful!")
        self.kik_authenticated = True
        print("Now I'm Authenticated, let's request roster")
        self.client.request_roster()

    def on_login_ended(self, response: LoginResponse):
        print(f"Full name: {response.first_name} {response.last_name}")
        self.my_jid = response.kik_node + "@talk.kik.com"
        print("Saved JID \"" + self.my_jid + "\" for refreshing!")

    def on_chat_message_received(self, chat_message: chatting.IncomingChatMessage):
        self.online_status = True
        from_jid = chat_message.from_jid

        print(f"[+] '{from_jid}' says: {chat_message.body}")

        global shuffle_word
        word = shuffle_word.get(from_jid)
        if word and chat_message.body and chat_message.body.strip() == word:
            shuffle_word[from_jid] = None
            global peers
            display = peers.get(from_jid, "User")
            self.client.send_chat_message(
                from_jid,
                f"...correct {display} 😮‍💨☝️\n\nYou have {atomic_incr(from_jid, display)} points"
            )
        else:
            print(f"{word} != {chat_message.body}")

        if not auth(from_jid):
            return

        for message in process_chat_message(chat_message, associated_jid=from_jid):
            self.client.send_chat_message(from_jid, message)

    def on_message_delivered(self, response: chatting.IncomingMessageDeliveredEvent):
        print(f"[+] Chat message with ID {response.message_id} is delivered.")


    def on_xiphias_get_users_response(self, response: Union[UsersResponse, UsersByAliasResponse]):
        for user in response.users:
            print(f"!! {user.display_name} {user.username}")

    def on_message_read(self, response: chatting.IncomingMessageReadEvent):
        print(f"[+] Human has read the message with ID {response.message_id}.")

    def on_group_message_received(self, chat_message: chatting.IncomingGroupChatMessage) -> None:
        group_jid = chat_message.group_jid

        print(f"[+] '{chat_message.from_jid}' from group ID {group_jid} says: {chat_message.body}")

        global shuffle_word
        global peers
        word = shuffle_word.get(group_jid)

        if word and chat_message.body and chat_message.body.strip() == word:
            shuffle_word[group_jid] = None
            display = peers.get(chat_message.from_jid, "User")
            self.client.send_chat_message(
                group_jid,
                f"...correct {display} 😮‍💨☝️\n\nYou have {atomic_incr(chat_message.from_jid, display)} points"
            )
        else:
            print(f"{word} != {chat_message.body}")

        if chat_message.body.strip().lower() == "frfrfr":
            self.client.send_chat_message(group_jid, "frfrfrfr 😮‍💨☝️")

        if chat_message.from_jid not in peers.keys():
            print(f"Requesting peer info for {chat_message.from_jid}")
            self.client.request_info_of_users(chat_message.from_jid)
            self.client.xiphias_get_users(chat_message.from_jid)

        if not auth(chat_message.from_jid):
            return

        for message in process_chat_message(chat_message, associated_jid=group_jid):
            self.client.send_chat_message(group_jid, message)

    def on_is_typing_event_received(self, response: chatting.IncomingIsTypingEvent):
        print(f'[+] {response.from_jid} is now {"" if response.is_typing else "not "}typing.')

    def on_group_is_typing_event_received(self, response: chatting.IncomingGroupIsTypingEvent):
        pass

    def on_roster_received(self, response: FetchRosterResponse):
        print("[+] Chat partners:\n" + '\n'.join([str(member) for member in response.peers]))

        users = [peer.jid for peer in response.peers if isinstance(peer, User)]

        self.client.xiphias_get_users(users)

    def on_friend_attribution(self, response: chatting.IncomingFriendAttribution):
        print(f"[+] Friend attribution request from {response.referrer_jid}")

    def on_image_received(self, image_message: chatting.IncomingImageMessage):
        print(f"[+] Image message was received from {image_message.from_jid}")

    def on_peer_info_received(self, response: PeersInfoResponse):
        print(f"[+] Peer info: {str(response.users)}")
        global peers
        for user in response.users:
            peers[user.jid] = user.display_name  # username is often "Username unavailable"
        print(peers)

    def on_group_status_received(self, response: chatting.IncomingGroupStatus):
        print(f"[+] Status message in {response.group_jid}: {response.status}")

    def on_group_receipts_received(self, response: chatting.IncomingGroupReceiptsEvent):
        print(f'[+] Received receipts in group {response.group_jid}: {",".join(response.receipt_ids)}')

    def on_status_message_received(self, response: chatting.IncomingStatusResponse):
        print(f"[+] Status message from {response.from_jid}: {response.status}")

    def on_username_uniqueness_received(self, response: UsernameUniquenessResponse):
        print(f"Is {response.username} a unique username? {response.unique}")

    def on_sign_up_ended(self, response: RegisterResponse):
        print(f"[+] Registered as {response.kik_node}")

    def on_connection_failed(self, response: ConnectionFailedResponse):
        print("Connection failed!")
        self.kik_authenticated = False

        print(f"[-] Connection failed: {response.message}")

    def on_login_error(self, login_error: LoginError):
        print("Kik login failed!")
        self.kik_authenticated = False

        if login_error.is_captcha():
            login_error.solve_captcha_wizard(self.client)

    def on_register_error(self, response: SignUpError):
        print(f"[-] Register error: {response.message}")

    def on_disconnected(self):
        print(f"\n!! Disconnected")

    def refresh(self) -> bool:
        try:
            self.online_status = False
            if not self.my_jid:
                print("Don't have my JID")
                return False

            self.client.send_chat_message(self.my_jid, "This is a message to myself to check if I am online.")
            time.sleep(2)
            if self.online_status:
                print("Bot is online!")
                return True

            self.kik_authenticated = None
            print("Reconnecting...")
            self.client.disconnect()
            self.connect()

            while not self.kik_authenticated:
                time.sleep(1)

            return self.kik_authenticated
        except Exception as e:
            traceback.print_exc()
            print(f"Something went wrong while refreshing! {e}")
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

    with open(args.credentials) as f:
        creds = yaml.safe_load(f)

    # set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(KikClient.log_format()))
    logger.addHandler(stream_handler)

    # create the bot
    bot = EchoBot(creds)

    while True:
        time.sleep(120)
        print("Refreshing...")
        while not bot.refresh():
            print("Refresh failed. Trying again soon...")
            time.sleep(30)
