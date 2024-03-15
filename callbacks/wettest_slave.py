from __future__ import annotations

import time
import traceback
import typing

import kik_unofficial.datatypes.xmpp.chatting as chatting  # type: ignore
from kik_unofficial.client import KikClient  # type: ignore
from kik_unofficial.callbacks import KikClientCallback  # type: ignore
from kik_unofficial.datatypes.xmpp.errors import LoginError  # type: ignore
from kik_unofficial.datatypes.xmpp.login import LoginResponse, ConnectionFailedResponse  # type: ignore

from callbacks.common.tempban import maybe_tempban, process_tempban
from log import get_logger
from auth import auth


logger = get_logger()


class WettestSlave(KikClientCallback):
    def __init__(self, creds: dict[str, typing.Any]):
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
