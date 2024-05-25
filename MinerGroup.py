
from VastInstance import VastInstance
from XenBlocksWallet import XenBlocksWallet


class MinerGroup:

    def __init__(self, balance: XenBlocksWallet, vast_instances: list[VastInstance]):
        self.id = balance.addr
        self.instances: list[VastInstance] = vast_instances
        self.balance: XenBlocksWallet = balance
        self.cost_ph = 0
        self.active_gpus = 0
        self.total_gpus = 0
        self.dflop = 0.0

        tot_flop = 0.0
        tot_cost = 0.0
        for ins in self.instances:
            self.cost_ph += ins.effective_cost_per_hour(0.04)
            self.total_gpus += ins.num_gpus

            if ins.is_running():
                self.active_gpus += ins.num_gpus
                tot_flop += ins.total_flops
                tot_cost += ins.cost_per_hour

        self.dflop = tot_flop / tot_cost if tot_cost > 0 else 0


    def get_block_count_for_address(self):
        return self.balance.block



