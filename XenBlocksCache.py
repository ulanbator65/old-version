
from XenBlocks import XenBlocks
from MinerStatistics import MinerStatistics
from cachetools import cached, TTLCache


ONE_MINUTE = 60

xenblocks = XenBlocks()


def get_miner_stats_for_address(addr: str) -> MinerStatistics:
    iterator = filter(lambda x: x.id.lower() == addr.lower(), __get_cache())
    return _get_first(iterator)


def get_miner_stats_for_rank(rank: int) -> MinerStatistics:
    iterator = filter(lambda x: x.rank == rank, __get_cache())
    return _get_first(iterator)


def get_miner_stats() -> list[MinerStatistics]:
    __get_cache.cache_clear()
    return __get_cache()


@cached(cache=TTLCache(maxsize=1, ttl=2*ONE_MINUTE))
def __get_cache() -> list[MinerStatistics]:
    print("XenBlocksCache loaded...")
    return xenblocks.get_miner_stats()


# Cache objects are mutable so return a copy
def _get_first(iterator) -> MinerStatistics:
    s: MinerStatistics = list(iterator)[0]
    return s.clone()
