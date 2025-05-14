from __future__ import annotations

import time
import traceback
import typing

from log import get_logger
from auth import auth


logger = get_logger()


class WettestSlave():
    def __init__(self, creds: dict[str, typing.Any]):
        self.online_status = False

    def on_chat_message_received(self, chat_message: typing.Any):
        from_id = chat_message.from_id

        if not auth(from_id):
            return

        raise NotImplemented()

    def on_group_message_received(self, chat_message: typing.Any) -> None:
        if not auth(chat_message.from_id):
            return

        raise NotImplemented()
