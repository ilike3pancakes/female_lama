from typing import Generator

from kik_unofficial.client import KikClient  # type: ignore
import kik_unofficial.datatypes.xmpp.chatting as chatting  # type: ignore

from log import get_logger


logger = get_logger()


group_to_last_status_user_jids = {}


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
