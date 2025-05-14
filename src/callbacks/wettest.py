from __future__ import annotations

from dataclasses import dataclass
import datetime
import random
from sqlite3 import Connection
import sys
import tempfile
import time
import traceback
import typing
from typing import Callable, Generator, Union, override

import discord

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


@dataclass
class VoiceNote:
    mp3_bytes: bytes


def process_authenticated_chat_message(
        client: discord.Client, message: typing.Any, *, associated_id: str, conn: typing.Any,
) -> Generator[str | bytes | VoiceNote, None, None]:
    wettest_math = "wettest math"
    wettest_shuffle = "wettest shuffle"
    wettest_urban = "wettest urban"
    wettest_trigger = "wettest trigger\n"
    message_body = message.content.lower()
    if message_body.startswith(wettest_math):
        yield calculate.calculate(message.content[len(wettest_math):].strip())
    elif message_body.startswith(wettest_shuffle):
        shuffled = reshuffle_word(associated_id)
        yield f"😮‍💨☝️🎲 {shuffled}"
    elif message_body.startswith(wettest_urban):
        yield f"😮‍💨☝️\n\n{urban(message.content[len(wettest_urban):].strip())}"
    elif message_body.startswith(wettest_trigger):
        result = create_trigger(message.content[len(wettest_trigger):])
        if result.success:
            yield "Aight ☝️"
            logger.info(f"Trigger created {result.value.prefix}\n{result.value.operation}")
            trigger_specs: TriggerSpecs = TriggerSpecs.read(
                "trigger_specs.yaml", default_ctor=TriggerSpecs.default_ctor
            )
            logger.info("Got trigger specs")
            trigger_specs.insert(associated_id, trigger=result.value)
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
        yield ai.wettest_dalle_image_of(message.content[len("wettest hallucinate "):])
    elif message_body.startswith("wettest vn "):
        yield "I'll record"
        completion = ai.wettest_gpt_completion_of(message.content[len("wettest vn "):])
        yield VoiceNote(mp3_bytes=ai.tts(completion))
    elif message_body.startswith("wettest"):
        username = Peers.get(message.author.id, conn=conn)
        friendly = "SpaceCat" in username if username else False
        yield ai.wettest_gpt_completion_of(message.content, friendly=friendly)
    elif len(message.content) == 1 and message.content in A_Z:
        username = Peers.get(message.author.id, conn=conn)
        if not username or not any(
            [
                "ilike3pancakes" in username,
                "spacecat4712" in username,
            ]
        ):
            return

        if not get_word():
            set_dictionary([shuffle.candidate().lower()])

        res = hangman(message_body)
        if res == "win":
            display = Peers.get(message.author.id, conn=conn) or "User"
            yield f"You did it {display} 😮‍💨\n\nYou have {atomic_incr(message.author.id, display)} points"
            set_dictionary([shuffle.candidate().lower()])
        elif res == "loss":
            display = Peers.get(message.author.id, conn=conn) or "User"
            yield f"{HANGMAN_STAGES[-1]}You killed him 😮‍💨☝️☝️☝️ good job {display}... Next time guess {get_word()} ☝️"
            set_dictionary([shuffle.candidate().lower()])
        elif res == None:
            pass
        else:
            logger.error(f"Unexpected hangman res {res}")
        yield get_state()


def reshuffle_word(associated_id: str) -> str:
    global shuffle_word
    new_shuffle_word = shuffle.candidate()
    shuffle_word[associated_id] = new_shuffle_word

    shuffled = list(new_shuffle_word)
    random.shuffle(shuffled)
    return ''.join(shuffled)


class Wettest(discord.Client):
    def __init__(self, *, sql: Connection, intents: discord.Intents):
        self.sql = sql
        super().__init__(intents=intents)

    @override
    async def on_ready(self) -> None:
        logger.info("Ready.")

    @override
    async def on_message(self, message: typing.Any):
        channel = message.channel
        channel_id = channel.id

        logger.info(f"[+] '{message.author.id}' from group ID {channel_id} says: {message.content}")

        t0 = datetime.datetime.utcnow()

        Peers.insert(conn=self.sql, jid=message.author.id, group_jid=channel_id)
        duration = datetime.datetime.utcnow() - t0
        logger.info(f"Updated peers.yaml in {duration}")

        display: str = Peers.get(message.author.id, conn=self.sql) or "User"

        peers = Peers.get_all_in_group_jid(group_jid=channel_id, conn=self.sql)
        group_peer_display_names = [peer.display_name for peer in peers if peer.display_name]

        global shuffle_word
        word = shuffle_word.get(channel_id)

        if word and message.content and message.content.strip() == word:
            shuffle_word[channel_id] = None
            await message.channel.send(
                f"...correct {display} 😮‍💨☝️\n\nYou have {atomic_incr(message.author.id, display)} points"
            )
            shuffled = reshuffle_word(channel_id)
            await message.channel.send(f"What about {shuffled} ? 😮‍💨☝️")
        elif word and message.content and len(message.content.strip().split(" ")) == 1:
            logger.info(f"Shuffle: {word} != {message.content}")

        trigger_specs: TriggerSpecs = TriggerSpecs.read("trigger_specs.yaml", default_ctor=TriggerSpecs.default_ctor)
        matching_trigger_specs = [spec for spec in trigger_specs.specs if spec.associated_jid == channel_id]
        matching_triggers = [create_trigger(spec.trigger_spec) for spec in matching_trigger_specs]
        matching_valid_triggers = [result.value for result in matching_triggers if result.success]
        for res in evaluate_all_triggers(message.content, matching_valid_triggers, group_peer_display_names, display):
            await message.channel.send(res)

        all_peers = Peers.get_all(conn=self.sql)
        if str(message.author.id) not in [peer.jid for peer in all_peers if peer.display_name]:
            logger.info(f"Unfamiliar peer {message.author=}")
            Peers.insert(conn=self.sql, jid=message.author.id, display_name=message.author.name, group_jid=message.guild.id)

        if not auth(message.author.id):
            return

        for message in process_authenticated_chat_message(self, message, associated_id=channel_id, conn=self.sql):
            if isinstance(message, str):
                await channel.send(message)
            elif isinstance(message, bytes):
                with tempfile.NamedTemporaryFile(suffix=".png") as tmpfile:
                    tmpfile.write(message)
                    tmpfile.seek(0)
                    await channel.send(file=discord.File(tmpfile.name))
            elif isinstance(message, VoiceNote):
                logger.info(f"Sending a voice note from {len(message.mp3_bytes)} mp3 bytes...")
                with tempfile.NamedTemporaryFile(suffix=".mp3") as tmpfile:
                    tmpfile.write(message.mp3_bytes)
                    tmpfile.seek(0)
                    await channel.send(file=discord.File(tmpfile.name))
                logger.info("Voice note sent!")
