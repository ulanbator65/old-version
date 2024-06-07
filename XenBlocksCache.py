
from XenBlocks import *
from db.DbCache import DbCache
from XenblocksBalanceCache import XenblocksBalanceCache
from LeaderboardCache import LeaderbordCache
from DifficultyCache import DifficultyCache
from cachetools import cached, TTLCache
import logger as log

ONE_MINUTE = 60

xenblocks = XenBlocks()

DIFFICULTY_KEY = "difficulty"


def get_difficulty() -> int:
    cache = DifficultyCache()
    value = DbCache().get_entity(cache)

    if value == 0:
        value = DbCache().get(cache.get_key()).value

    return value


def get_balance(addr: str) -> int:
    cache = XenblocksBalanceCache(addr)
    return DbCache().get_entity(cache)


def get_wallet_balance(addr: str, timestamp_s: int) -> XenBlocksWallet:
    row = _get_cached_wallet_balance(addr)
    return xenblocks.map_row(row, timestamp_s)


def get_balance_for_rank(rank: int, timestamp_s: int) -> XenBlocksWallet:

    cache = LeaderbordCache()
    cached_value: str = DbCache().get_entity(cache)

    if not cached_value:
        return None

    tbody: list = get_elements("<tbody>", "</tbody>", cached_value)
    rows: list = get_elements("<tr>", "</tr>", tbody[0])

    row = rows[rank-1]
    return XenBlocks().map_row(row, timestamp_s)


def _get_cached_wallet_balance(addr: str) -> str:
    max_age_seconds = 4 * 3600
    cach_entry = DbCache().get(addr)

    if not cach_entry or cach_entry.is_expired(max_age_seconds):
        cached_response: list[str] = xenblocks.get_xenblocks_balance()

        # Call to endpoint was not successfull - fallback on older DB Cache value
        if (not cached_response or len(cached_response) == 0) and cach_entry:
            return cach_entry.value

        rows = list(filter(lambda x: addr.lower() in x, cached_response))
        row = rows[0]
        DbCache().update(addr, row)
        return row

    return cach_entry.get_value()

