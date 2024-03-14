import logging
import sys


logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logging.getLogger("kik_unofficial").setLevel(logging.WARN)

def get_logger():
    return logger
