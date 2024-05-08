
from datetime import datetime
from VastInstance import VastInstance
from XenBlocksWallet import XenBlocksWallet
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo


class MinerGroup:

    def __init__(self, balance: XenBlocksWallet, balance_history: list[XenBlocksWallet], vast_instances: list[VastInstance]):
        self.id = balance.addr
        self.instances: list[VastInstance] = vast_instances
        self.balance: XenBlocksWallet = balance
        self.balance_history = balance_history
        self.cost_ph = 0
        self.db = XenBlocksWalletHistoryRepo()

#        active_miners = list(filter(lambda x: x.is_running(), self.instances))
#        self.active_miners: int = len(active_miners)
        self.active_gpus = 0
        self.total_gpus = 0

        for ins in self.instances:
            self.cost_ph += ins.effective_cost_per_hour(0.04)
            self.total_gpus += ins.num_gpus

            if ins.is_running():
                self.active_gpus += ins.num_gpus


    def get_delta(self, hours: float) -> XenBlocksWallet:
        if not self.balance or not self.balance_history:
            return None

        historic_balance = self.select_snapshot_from_history(hours)
        if not historic_balance:
            return None

        return self.balance.difference(historic_balance)


    def duration(self, age_in_hours: int) -> float:
        if not self.balance or not self.balance_history:
            return 0.0

        historic_balance = self.select_snapshot_from_history(age_in_hours)
        if not historic_balance:
            return 0.0

        return self.balance.difference(historic_balance).timestamp_s / 3600


    def block_rate_per_hour(self, age_in_hours: int) -> float:
        if not self.balance or not self.balance_history:
            return 0.0

        historic_balance = self.select_snapshot_from_history(age_in_hours)
        if not historic_balance:
            return 0.0

        delta_balance = self.balance.difference(historic_balance)

        tdelta = delta_balance.timestamp_s
        tdelta = tdelta/3600
        print("Hours: ", age_in_hours)
        print("TDelta: ", tdelta)
        print("mg: ", delta_balance.block)
        print("snap: ", delta_balance.block)
        block_delta = delta_balance.block
        xuni_delta = delta_balance.xuni

        return block_delta / tdelta



    def block_rate_per_day(self) -> float:
        if not self.balance or not self.balance_history:
            return 0.0

        historic_balance = self.select_snapshot_from_history(24)
        if not historic_balance:
            return 0.0
            # return self.block_rate_per_hour(1) * 24

        delta_balance = self.balance.difference(historic_balance)

        block_delta = delta_balance.block
        xuni_delta = delta_balance.xuni

        return block_delta


    def select_snapshot_from_history(self, age_hours: float, max_deviation_h: float = 0.6) -> XenBlocksWallet:

        timestamp_s = self.balance.timestamp_s - (3600 * age_hours)

        print("Search for: ", datetime.fromtimestamp(timestamp_s))

        for h in self.balance_history:

            diff_h: float = (timestamp_s - h.timestamp_s) / 3600

            if abs(diff_h) < max_deviation_h:
                print("Found: ", datetime.fromtimestamp(h.timestamp_s))
                print("Diff: ", diff_h)
                return h

            if h.timestamp_s < timestamp_s:
                print("Found: ", datetime.fromtimestamp(h.timestamp_s))
                diff_h: float = (timestamp_s - h.timestamp_s) / 3600
                print("Diff: ", diff_h)

                # Don't allow the historic value to deviate more than 1 hour (or 'max_deviation')
                if abs(diff_h) > max_deviation_h:
                    return None

                return h

        return None


    def get_block_count_for_address(self):
        return self.balance.block


    def effect(self) -> float:
        if self.total_gpus == 0:
            return 0
        return self.active_gpus / self.total_gpus


