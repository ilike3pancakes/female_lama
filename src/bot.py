#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
import typing
import yaml

from callbacks.wettest import Wettest
from callbacks.wettest_slave import WettestSlave
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

    # create slave bots
    slave_bots = [WettestSlave(slave_creds) for slave_creds in creds.get("slaves") if "slaves" in creds.keys()]

    # create the bot
    bot = Wettest(creds=creds, sql=conn)

    while True:
        time.sleep(120)
        while not bot.refresh():
            logger.info("Refresh failed. Trying again soon...")
            time.sleep(30)

        for slave_bot in slave_bots:
            if not slave_bot.refresh():
                logger.info(f"Slave bot {slave_bot.my_jid} refresh failed.")
