import logging.config
from pathlib import Path

from bot_managers import settings as bot_settings
from environs import Env
from tg_logger.settings import configure_logger

env = Env()
env.read_env()


BASE_DIR = Path(__file__).resolve().parent.parent

SESSION_ROOT = BASE_DIR / 'sessions'

DB_SCHEMA_DUMP_PATH = BASE_DIR / 'tests' / 'setup' / 'dump.sql'

POSTGRES_CONFIG = {
    'POSTGRES_USER': env.str('POSTGRES_USER'),
    'POSTGRES_PASSWORD': env.str('POSTGRES_PASSWORD'),
    'POSTGRES_HOST': env.str('DB_HOST'),
    'POSTGRES_PORT': env.str('DB_PORT'),
    'POSTGRES_DB': env.str('DB_NAME'),
}

ASYNCPG_TIMEOUT = 20
MAX_RETRIES_DB_REQUESTS = 3
RETRY_DELAY_DB_REQUESTS = 1

ADMIN_BOT_TOKEN = env.str('ADMIN_BOT_TOKEN')
ADMIN_SENDER_ID = env.int('ADMIN_SENDER_ID')


REDIS_CACHE_CONFIG = {
    'REDIS_HOST': env.str('REDIS_HOST'),
    'REDIS_PORT': env.str('REDIS_PORT'),
}

REDIS_HOST_PORT = env.int('REDIS_HOST_PORT', default=22)
REDIS_HOST_USER = env.str('REDIS_HOST_USER', default='')
REDIS_HOST_PASSWORD = env.str('REDIS_HOST_PASSWORD', default='')
REDIS_HOST_CONTAINER = env.str('REDIS_HOST_CONTAINER', default='')
REDIS_LISTENER_DB = 0
REDIS_RESPONSIBLE_DB = 1


FURY_AUTH = env.str('FURY_AUTH')

# Project settings
NUMBER_OF_MANAGERS = env.int('NUMBER_OF_MANAGERS', default=2)
DEFAULT_REQUEST_RETRY_DELAYS = (1, 4, 10)

# Logger settings
LOGGER_CONFIG = configure_logger(ADMIN_BOT_TOKEN, ADMIN_SENDER_ID)
CONSOLE_LOGLEVEL = env.str('CONSOLE_LOGLEVEL', 'info').upper()
FILE_LOGLEVEL = env.str('FILE_LOGLEVEL', 'info').upper()

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': CONSOLE_LOGLEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'level': FILE_LOGLEVEL,
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': '/etc/aio_offer_bot/logger_file.log',
        },
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['file', 'console'],
        },
        'app': {
            'level': 'INFO',
            'handlers': ['file', 'console'],
            'propagate': False,
        },
    },
})

LAST_EVENT_EXPIRES_SECONDS = env.int('LAST_EVENT_EXPIRES_SECONDS', 60)

# Bot managers settings
bot_settings.LOGGER_SETTINGS = LOGGER_CONFIG
bot_settings.NUMBER_OF_MANAGERS = NUMBER_OF_MANAGERS
bot_settings.DEFAULT_REQUEST_RETRY_DELAYS = DEFAULT_REQUEST_RETRY_DELAYS

CHANEL_CHECKER_URL = env.str('CHANEL_CHECKER_URL', default="http://127.0.0.1:8080")

TEST_RUN = env.bool('TEST_RUN', default=False)

STATE_MACHINE_REDIS_DB = 2


# Redis errors
REDIS_MAX_CONNECT_ATTEMPTS = 3
REDIS_RECONNECT_DELAY_SECONDS = 10
REDIS_MAX_RETRY_ATTEMPTS = 5
REDIS_RETRY_DELAY_SECONDS = 2

PROXYS = env.list('PROXYS', delimiter=' ', default=[])
