from tg_logger import BaseLogger
from tg_logger.settings import configure_logger

from config import ADMIN_BOT_TOKEN, ADMIN_SENDER_ID

configure_logger(ADMIN_BOT_TOKEN, ADMIN_SENDER_ID)


def get_logger():
    return BaseLogger()
