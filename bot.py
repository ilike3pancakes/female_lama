#!/usr/bin/env python3

import argparse
import logging
import sys
import time
import traceback
from typing import Generator
import yaml

import kik_unofficial.datatypes.xmpp.chatting as chatting  # type: ignore
from kik_unofficial.client import KikClient  # type: ignore
from kik_unofficial.callbacks import KikClientCallback  # type: ignore
from kik_unofficial.datatypes.xmpp.errors import SignUpError, LoginError  # type: ignore
from kik_unofficial.datatypes.xmpp.roster import FetchRosterResponse, PeersInfoResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.sign_up import RegisterResponse, UsernameUniquenessResponse  # type: ignore
from kik_unofficial.datatypes.xmpp.login import LoginResponse, ConnectionFailedResponse  # type: ignore

import ai
import calculate
from auth import auth


def process_chat_message(message: chatting.IncomingChatMessage) -> Generator[str, None, None]:
    if message.body.lower().startswith("wettest math"):
        yield calculate.calculate(message.body.split("wettest math")[1].strip())
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

        print(f"[+] '{chat_message.from_jid}' says: {chat_message.body}")
        print("[+] Replaying.")

        if not auth(chat_message.from_jid):
            return

        for message in process_chat_message(chat_message):
            self.client.send_chat_message(chat_message.from_jid, message)

    def on_message_delivered(self, response: chatting.IncomingMessageDeliveredEvent):
        print(f"[+] Chat message with ID {response.message_id} is delivered.")

    def on_message_read(self, response: chatting.IncomingMessageReadEvent):
        print(f"[+] Human has read the message with ID {response.message_id}.")

    def on_group_message_received(self, chat_message: chatting.IncomingGroupChatMessage):
        print(f"[+] '{chat_message.from_jid}' from group ID {chat_message.group_jid} says: {chat_message.body}")

        if not auth(chat_message.from_jid):
            return

        for message in process_chat_message(chat_message):
            self.client.send_chat_message(chat_message.group_jid, message)

    def on_is_typing_event_received(self, response: chatting.IncomingIsTypingEvent):
        print(f'[+] {response.from_jid} is now {"" if response.is_typing else "not "}typing.')

    def on_group_is_typing_event_received(self, response: chatting.IncomingGroupIsTypingEvent):
        pass

    def on_roster_received(self, response: FetchRosterResponse):
        print("[+] Chat partners:\n" + '\n'.join([str(member) for member in response.peers]))

    def on_friend_attribution(self, response: chatting.IncomingFriendAttribution):
        print(f"[+] Friend attribution request from {response.referrer_jid}")

    def on_image_received(self, image_message: chatting.IncomingImageMessage):
        print(f"[+] Image message was received from {image_message.from_jid}")

    def on_peer_info_received(self, response: PeersInfoResponse):
        print(f"[+] Peer info: {str(response.users)}")

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
