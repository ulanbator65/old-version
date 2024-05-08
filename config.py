
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv('API_KEY')
ADDR = os.getenv('ADDR')
VAST_IMAGE = os.getenv('VAST_IMAGE')

MANUAL_MODE = (os.getenv('MANUAL_MODE') == 'True')
SHOW_MINER_GROUPS = (os.getenv('SHOW_MINER_GROUPS') == 'True')
RUN_STATE_MACHINES = (os.getenv('RUN_STATE_MACHINES') == 'True')

DB_NAME = "../database.db"
HISTORY_DB = "../history-db.db"


BID_INCREASE_PCT = 0
OVERRIDE_BID = True


def get_int_list(name: str) -> list:
    all = os.getenv(name).split(",")
    result = []
    for e in all:
        result.append(int(e.strip()))

    return result


# Older configuration, possibly obsolete
BLACKLIST = get_int_list('BLACKLIST')
WHITELIST = get_int_list('WHITELIST')
RESERVED_INSTANCES = get_int_list('RESERVED_INSTANCES')

