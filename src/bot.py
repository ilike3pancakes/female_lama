#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
import typing
import yaml

import discord

from callbacks.wettest import Wettest
from log import get_logger


logger = get_logger()

conn = sqlite3.connect("prod.db", check_same_thread=False)


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
        creds: dict[str, typing.Any] = yaml.safe_load(f)

    intents = discord.Intents.default()
    intents.message_content = True

    bot = Wettest(sql=conn, intents=intents)

    bot.run(creds["token"])
