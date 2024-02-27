import logging
import sys

from kik_unofficial.client import KikClient  # type: ignore


logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
# stream_handler.setFormatter(logging.Formatter(KikClient.log_format()))
logger.addHandler(stream_handler)

def get_logger():
    return logger
