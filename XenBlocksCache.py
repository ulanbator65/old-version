
from XenBlocksWallet import XenBlocksWallet
from XenBlocks import XenBlocks
from cachetools import cached, TTLCache


ONE_MINUTE = 60

xenblocks = XenBlocks()


def get_wallet_snapshot(addr: str) -> XenBlocksWallet:
    iterator = filter(lambda x: x.addr.lower() == addr.lower(), __get_cache())
    latest = _get_first(iterator)
    print("Latest: ", latest)
    return latest


def get_miner_stats_for_rank(rank: int) -> XenBlocksWallet:
    iterator = filter(lambda x: x.rank == rank, __get_cache())
    return _get_first(iterator)


def get_miner_stats() -> list[XenBlocksWallet]:
    __get_cache.cache_clear()
    return __get_cache()


@cached(cache=TTLCache(maxsize=1, ttl=ONE_MINUTE))
def __get_cache() -> list[XenBlocksWallet]:
    print("XenBlocksCache loaded...")
    return xenblocks.get_miner_stats()


# Cache objects are mutable so return a copy
def _get_first(iterator) -> XenBlocksWallet:
    return list(iterator)[0].clone()
