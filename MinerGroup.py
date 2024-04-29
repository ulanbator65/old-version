

from VastInstance import VastInstance
from MinerStatistics import *
from XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from XenBlocksWallet import XenBlocksWallet


class MinerGroup:

    def __init__(self, stats: MinerStatistics, vast_instances: list[VastInstance]):
        self.id = stats.id.lower()
        self.instances: list[VastInstance] = vast_instances
        self.stats = stats
        self.historic_snapshot = None
        self.db = XenBlocksWalletHistoryRepo()

        active_miners = list(filter(lambda x: x.is_running(), self.instances))
        self.total_miners: int = len(self.instances)
        self.active_miners: int = len(active_miners)


    def effect(self) -> float:
        if self.total_miners <= 0:
            return 0
        return self.active_miners / self.total_miners


    def calculate_totals(self, instances: list):

        for ins in instances:
            self.stats.cost_per_hour += ins.cost_per_hour
            # Miner total stats
#            stats = ins.miner


