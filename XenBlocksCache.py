
from datetime import datetime
from XenBlocksWallet import XenBlocksWallet
from XenBlocks import XenBlocks
from db.DbCache import DbCache
from cachetools import cached, TTLCache
import logger as log

MINUTES = 60

xenblocks = XenBlocks()

DIFFICULTY_KEY = "difficulty"


def get_difficulty() -> int:
    ttl_s = 20

    cache_entry = DbCache().get(DIFFICULTY_KEY)
    if not cache_entry:
        return _get_difficulty()

    print(cache_entry[2])

    age = datetime.now().timestamp() - int(cache_entry[1])
    if age > ttl_s:
        value = _get_difficulty()

    return int(cache_entry[2])


#@cached(cache=TTLCache(maxsize=1, ttl=1*MINUTES))
def _get_difficulty() -> int:
    value = xenblocks.get_difficulty()
    timestamp = datetime.now().timestamp()

    DbCache().update(DIFFICULTY_KEY, str(value))
    return value


def get_wallet_balance(addr: str, timestamp_s: int) -> XenBlocksWallet:
    row = _get_cached_wallet_balance(addr)
    return xenblocks.map_row(row, timestamp_s)


def get_balance_for_rank(rank: int, timestamp_s: int) -> XenBlocksWallet:
    cache = __get_wallet_cache()
    if len(cache) == 0:
        return None

    return xenblocks.map_row(cache[rank-1], timestamp_s)


def get_balance_for_rank(rank: int, timestamp_s: int) -> XenBlocksWallet:
    age_seconds = 0
    key = f"rank:{rank}"
    cach_entry = DbCache().get(key)

    if cach_entry:
        age_seconds = datetime.now().timestamp() - cach_entry[1]

    if not cach_entry or age_seconds > 30:
        cached_response: list[str] = __get_wallet_cache()

        row = cached_response[rank-1]
        DbCache().update(key, row)

        return xenblocks.map_row(row, timestamp_s)

    return xenblocks.map_row(cach_entry[2], timestamp_s)


@cached(cache=TTLCache(maxsize=1, ttl=MINUTES))
def __get_wallet_cache() -> list[str]:
    print("XenBlocksCache loaded...")
    return xenblocks.get_xenblocks_balance()


def _get_cached_wallet_balance(addr: str) -> str:
    age_seconds = 0
    cach_entry = DbCache().get(addr)

    if cach_entry:
        age_seconds = datetime.now().timestamp() - cach_entry[1]

    if not cach_entry or age_seconds > 30:
        cached_response: list[str] = __get_wallet_cache()

        rows = list(filter(lambda x: addr.lower() in x, cached_response))
        row = rows[0]
        DbCache().update(addr, row)
        return row

    return cach_entry[2]

