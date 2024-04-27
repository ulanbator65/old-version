
from XenBlocks import XenBlocks
from MinerStatistics import MinerStatistics
from Time import Time
import copy

ONE_MINUTE = 60


class XenBlocksMinerStats:

    def __init__(self, xen_blocks=XenBlocks(), time_to_live: int = 2*ONE_MINUTE):
        self.xen_blocks = xen_blocks
        self.time_to_live: int = time_to_live
        self.data: list[MinerStatistics] = []


    def get(self, address: str, min_age_hours: int = 0) -> MinerStatistics:
        self._load_cache()

        stats = list(filter(lambda x: x.id.lower() == address.lower(), self.data))

        # Make sure to returnn a copy of the cached object
        return copy.deepcopy(stats[0])


    def _load_cache(self):
        if self._cache_expired():
            self.data = self.xen_blocks.get_miner_stats()
            print("Cache loaded!!!")


    def _cache_expired(self) -> bool:
        t1 = self._get_age_in_seconds()
        now = Time.now().get_age_in_seconds(0)
        return now > (t1 + self.time_to_live)


    def _get_age_in_seconds(self) -> int:
        if not self.data:
            return self.time_to_live + 9999999

        return self.data[0].timestamp_s

