
from XenBlocksWallet import XenBlocksWallet
from XenBlocks import XenBlocks
from cachetools import cached, TTLCache
import logger as log

MINUTES = 60

xenblocks = XenBlocks()


@cached(cache=TTLCache(maxsize=1, ttl=59*MINUTES))
def get_difficulty() -> int:
    return xenblocks.get_difficulty()


def get_wallet_balance(addr: str, timestamp_s: int) -> XenBlocksWallet:
    cache = __get_cache()
    if len(cache) == 0:
        return None

    if len(cache) < 1000:
        log.print_error("Cache contained less than 1000 wallet balances - expected several thousands!")
        return None

    rows = list(filter(lambda x: addr.lower() in x, cache))
    row = rows[0]
    return xenblocks.map_row(row, timestamp_s)


def get_balance_for_rank(rank: int, timestamp_s: int) -> XenBlocksWallet:
    cache = __get_cache()
    if len(cache) == 0:
        return None

    return xenblocks.map_row(cache[rank-1], timestamp_s)


@cached(cache=TTLCache(maxsize=1, ttl=MINUTES))
def __get_cache() -> list[str]:
    print("XenBlocksCache loaded...")
    return xenblocks.get_xenblocks_balance()

