
from XenBlocksWallet import XenBlocksWallet
from XenBlocks import XenBlocks
from cachetools import cached, TTLCache


ONE_MINUTE = 60

xenblocks = XenBlocks()


def get_wallet_snapshot(addr: str) -> XenBlocksWallet:
    cache = __get_cache()
    if len(cache) == 0:
        return None

    iterator = filter(lambda x: x.addr.lower() == addr.lower(), cache)
    return _get_first(iterator)


def get_miner_stats_for_rank(rank: int) -> XenBlocksWallet:
    cache = __get_cache()
    if len(cache) == 0:
        return None

    iterator = filter(lambda x: x.rank == rank, cache)
    return _get_first(iterator)


def get_miner_stats() -> list[XenBlocksWallet]:
    __get_cache.cache_clear()
    return __get_cache()


@cached(cache=TTLCache(maxsize=3, ttl=ONE_MINUTE))
def __get_cache() -> list[XenBlocksWallet]:
    print("XenBlocksCache loaded...")
    return xenblocks.get_miner_stats()


# Cache objects are mutable so return a copy
def _get_first(iterator) -> XenBlocksWallet:
    return list(iterator)[0].clone()
