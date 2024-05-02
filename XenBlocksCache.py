
from XenBlocksWallet import XenBlocksWallet
from XenBlocks import XenBlocks
from cachetools import cached, TTLCache


ONE_MINUTE = 60

xenblocks = XenBlocks()


def get_wallet_balance(addr: str) -> XenBlocksWallet:
    cache = __get_cache()
    if len(cache) == 0:
        return None

    iterator = filter(lambda x: addr.lower() in x, cache)
    row = _get_first_row(iterator)
    return xenblocks.map_row(row)


def get_balance_for_rank(rank: int) -> XenBlocksWallet:
    cache = __get_cache()
    if len(cache) == 0:
        return None

    return xenblocks.map_row(cache[rank-1])


@cached(cache=TTLCache(maxsize=3, ttl=ONE_MINUTE))
def __get_cache() -> list[str]:
    print("XenBlocksCache loaded...")
    return xenblocks.get_miner_stats()


def _get_first_row(iterator) -> str:
    return list(iterator)[0]
