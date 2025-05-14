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

import ai
import calculate
from auth import auth
from hangman import set_dictionary, hangman, get_state, get_word, HANGMAN_STAGES
from log import get_logger
from peers import Peers
from points import atomic_incr
import shuffle
from trigger import create_trigger, evaluate_all_triggers, TriggerSpecs
from urban import urban


shuffle_word = dict()

logger = get_logger()

A_Z = set("abcdefghijklmnopqrstuvwxyz".upper())

async_queue: list[Callable[[], None]] = []


@dataclass
class VoiceNote:
    mp3_bytes: bytes


def process_authenticated_chat_message(
        client: typing.Any, message: typing.Any, *, associated_jid: str, conn: typing.Any,
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
        yield VoiceNote(mp3_bytes=ai.tts(completion))
    elif message_body.startswith("wettest"):
        username = Peers.get(message.from_jid, conn=conn)
        friendly = "SpaceCat" in username if username else False
        yield ai.wettest_gpt_completion_of(message.body, friendly=friendly)
    elif len(message.body) == 1 and message.body in A_Z:
        username = Peers.get(message.from_jid, conn=conn)
        if not username or not any(
            [
                "Blake" in username,
                "SpaceCat" in username,
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


class Wettest():
    def __init__(self, *, creds: typing.Any, sql: Connection):
        self.creds = creds
        self.sql = sql

        self.client = Client(self)

    def on_chat_message_received(self, chat_message: typing.Any):
        from_id = chat_message.from_id

        global shuffle_word
        word = shuffle_word.get(from_id)
        if word and chat_message.body and chat_message.body.strip() == word:
            shuffle_word[from_id] = None
            display = Peers.get(from_id, conn=self.sql) or "User"
            self.client.send_chat_message(
                from_id,
                f"...correct {display} 😮‍💨☝️\n\nYou have {atomic_incr(from_id, display)} points"
            )
            shuffled = reshuffle_word(from_id)
            self.client.send_chat_message(from_id, f"What about {shuffled} ? 😮‍💨☝️")
        elif word and chat_message.body and len(chat_message.body.strip().split(" ")) == 1:
            logger.info(f"{word} != {chat_message.body}")

        trigger_specs: TriggerSpecs = TriggerSpecs.read("trigger_specs.yaml", default_ctor=TriggerSpecs.default_ctor)
        matching_trigger_specs = [spec for spec in trigger_specs.specs if spec.associated_jid == from_id]
        matching_triggers = [create_trigger(spec.trigger_spec) for spec in matching_trigger_specs]
        matching_valid_triggers = [result.value for result in matching_triggers if result.success]
        for res in evaluate_all_triggers(chat_message.body, matching_valid_triggers, ["No one"], "Bruv"):
            self.client.send_chat_message(from_id, res)

        if not auth(from_id):
            return

        try:
            for message in process_authenticated_chat_message(self.client, chat_message, associated_jid=from_id, conn=self.sql):
                if isinstance(message, str):
                    self.client.send_chat_message(from_id, message)
                elif isinstance(message, bytes):
                    self.client.send_chat_image(from_id, message)
                elif isinstance(message, VoiceNote):
                    logger.info(f"Sending a voice note from {len(message.mp3_bytes)} mp3 bytes...")
                    send_vn(self.client, from_id, message.mp3_bytes, is_group=False)
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

        logger.info(f"[+] '{chat_message.from_id}' from group ID {group_jid} says: {chat_message.body}")

        # Async processing hack.
        if len(async_queue):
            logger.info(f"Async processing {len(async_queue)}")
            try:
                async_queue.pop(0)()
            except Exception as e:
                logger.error(f"Exception in async processing {e}")

        t0 = datetime.datetime.utcnow()

        Peers.insert(conn=self.sql, jid=chat_message.from_id, group_jid=group_jid)
        duration = datetime.datetime.utcnow() - t0
        logger.info(f"Updated peers.yaml in {duration}")

        display: str = Peers.get(chat_message.from_id, conn=self.sql) or "User"

        peers = Peers.get_all_in_group_jid(group_jid=group_jid, conn=self.sql)
        group_peer_display_names = [peer.display_name for peer in peers if peer.display_name]

        global shuffle_word
        word = shuffle_word.get(group_jid)

        if word and chat_message.body and chat_message.body.strip() == word:
            shuffle_word[group_jid] = None
            self.client.send_chat_message(
                group_jid,
                f"...correct {display} 😮‍💨☝️\n\nYou have {atomic_incr(chat_message.from_id, display)} points"
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
        if chat_message.from_id not in [peer.jid for peer in all_peers if peer.display_name]:
            logger.info(f"Requesting peer info for {chat_message.from_id}")
            self.client.request_info_of_users(chat_message.from_id)
            self.client.xiphias_get_users(chat_message.from_id)

        if not auth(chat_message.from_id):
            return

        for message in process_authenticated_chat_message(self.client, chat_message, associated_jid=group_jid, conn=self.sql):
            if isinstance(message, str):
                self.client.send_chat_message(group_jid, message)
            elif isinstance(message, bytes):
                self.client.send_chat_image(group_jid, message)
            elif isinstance(message, VoiceNote):
                logger.info(f"Sending a voice note from {len(message.mp3_bytes)} mp3 bytes...")
                send_vn(self.client, group_jid, message.mp3_bytes, is_group=True)
                logger.info("Voice note sent!")
