
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv('API_KEY')
ADDR = os.getenv('ADDR')
VAST_IMAGE = os.getenv('VAST_IMAGE')

MAX_GPU = os.getenv('MAX_GPU')

MANUAL_MODE = (os.getenv('MANUAL_MODE') == 'True')
SHOW_MINER_GROUPS = (os.getenv('SHOW_MINER_GROUPS') == 'True')

DB_NAME = "../database.db"
HISTORY_DB = "../history.db"
CACHE_DB = "../cache.db"


BID_INCREASE_PCT = 0
OVERRIDE_BID = True


def get_int_list(name: str) -> list:
    all = os.getenv(name).split(",")
    result = []
    for e in all:
        result.append(int(e.strip()))

    return result


def get_list(name: str) -> list[str]:
    all = os.getenv(name).split(",")
    result = []
    for e in all:
        result.append(e.strip().upper())

    return result


RUN_STATE_MACHINES = get_list('RUN_STATE_MACHINES')


# Older configuration, possibly obsolete
BLACKLIST = [6011840, 9563671, 9355268, 9355256, 9355269, 9355271, 6011841, 9355272]

BLACKLIST2 = get_int_list('BLACKLIST')
WHITELIST = get_int_list('WHITELIST')
RESERVED_INSTANCES = get_int_list('RESERVED_INSTANCES')

