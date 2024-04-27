

from VastInstance import VastInstance
from MinerStatistics import *
from MinerStatisticsHistoryRepo import MinerStatisticsHistoryRepo
import XenBlocksCache as Cache


class MinerGroup:

    def __init__(self, id: str, vast_instances: list[VastInstance]):
        self.id = id.lower()
        self.instances: list[VastInstance] = vast_instances
        self.stats = Cache.get_miner_stats_for_address(id)
        self.db = MinerStatisticsHistoryRepo()

        active_miners = list(filter(lambda x: x.is_running(), self.instances))
        self.total_miners: int = len(self.instances)
        self.active_miners: int = len(active_miners)


    def subtract(self, other: MinerStatistics):
        duration_seconds = self.stats.timestamp_s - other.timestamp_s
        self.stats.duration_hours = round(duration_seconds / 3600, 1)
        self.stats.block = (self.stats.block - other.block)
        self.stats.super = (self.stats.super - other.super)
        self.stats.xuni = (self.stats.xuni - other.xuni)


    def effect(self) -> float:
        if self.total_miners <= 0:
            return 0
        return self.active_miners / self.total_miners


    def calculate_totals(self, instances: list):

        for ins in instances:
            self.stats.cost_per_hour += ins.cost_per_hour
            # Miner total stats
#            stats = ins.miner


