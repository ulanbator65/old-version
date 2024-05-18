
from VastInstance import VastInstance
from VastClient import VastClient
from Field import Field
from MinerStatistics import *
from constants import *

import config

from VastMinerRealtimeTable import VastMinerRealtimeTable


class InstanceTable:

    def __init__(self, vast: VastClient = VastClient(config.API_KEY, config.BLACKLIST)):
        self.vast = vast
        self.instances: list[VastInstance] = []
        self.snapshot_time: datetime = datetime.now()
        # Statistics
        self.miner_stats = None
        self.tot_hashrate = 0
        self.tot_hashrate_per_dollar = 0
        self.tot_cost: float = 0
        self.tot_block: int = 0
        self.tot_super: int = 0
        self.tot_XUNI: int = 0
        self.tot_block_rate: float = 0
        self.tot_block_cost: float = 0


    def total_block_per_day(self) -> float:
        return 24 * self.tot_block_rate

    def len(self) -> int:
        return len(self.instances)


    def get_instance(self, id: int) -> VastInstance:
        for inst in self.instances:
            if inst.id == id:
                return inst
        return None


    def refresh(self):
#        if self.should_refresh_cache():
#            self.instances = self.vast.get_instances()
#            self.snapshot_time = datetime.now()
#        else:
#            self.refresh_miner_stats()

        self.snapshot_time = datetime.now()
        if config.MANUAL_MODE is False:
            self.instances = self.get_instances_for_address(config.ADDR)
        else:
#            self.instances = self.get_instances_for_address(config.ADDR)
            self.instances = self.get_manual_instances()

#        self.instances = self.vast.get_instances()
        self.load_miner_stats()
#        self.housekeeping()


    def load_miner_stats(self):
        self.vast.load_miner_data(self.instances)
        self.sort_on_hashrate_per_dollar()
#        self.snapshot_time = datetime.now()

#        for inst in self.instances:
#            if inst.miner:
#                inst.miner.normalize(inst.get_age_in_hours())


    def housekeeping(self):
        for inst in self.instances:
            if inst.needs_reboot():
#                self.vast.reboot_instance(inst.id)
                print(f"Rebooting id={inst.id} due to: Low hashrate per USD!")
                print(f"Hashrate: {inst.hashrate_per_dollar()}")


    def get_managed_instances(self) -> 'InstanceTable':
        iterator = filter(lambda x: x.is_managed, self.instances)

        managed_instances = list(iterator)
        table = InstanceTable(self.vast)
        table.instances = managed_instances
        return table


    def get_instances_for_address(self, addr: str) -> list:
        all_instances = self.vast.get_instances()

        filtered_list = list(filter(lambda x: x.addr and x.addr.lower() == addr.lower(), all_instances))

        # Auto reset when block count is negative (due to offset calculation)
#        for inst in filtered_list:
#            if inst.is_miner_online() and inst.miner.block < -0.1:
#                inst.reset_hours()

        return filtered_list


    def get_manual_instances(self) -> list:
        all_instances = self.vast.get_instances()

        iterator = filter(lambda x: not x.is_managed, all_instances)
        return list(iterator)


    def sort_on_hashrate_per_dollar(self):
        hpd = lambda x: x.miner.hashrate_per_dollar() if x.miner else 0.0
#        self.instances = sorted(self.instances, key=lambda inst: (inst.hashrate_per_dollar2()))
        self.instances = sorted(self.instances, key=hpd, reverse=True)

    def sort_on_cost(self):
        self.instances = sorted(self.instances, key=lambda inst: (inst.block_cost()))


    def get_id_for_row(self, row_nr) -> int:
        return self.get_instance_for_row(row_nr).id


    def get_instance_for_row(self, row_nr) -> VastInstance:
        return self.instances[row_nr - 1]


    def get_ids_for_index(self, index: list) -> list:
        return [self.instances[num - 1].id for num in index]


    def should_refresh_cache(self):
        if len(self.instances) == 0:
            return True

        print("Table age; ", self.data_age())
        return self.data_age() > 60.0


    # Age used for cacheing
    def data_age(self):
        return (datetime.now() - self.snapshot_time).total_seconds()


    def reset_hours(self):
        min_hours = 0.2
        for instance in self.instances:
            if instance.miner:
#                if instance.miner.block_cost() > 0.5 or\
#                    (instance.miner.duration_hours > 10 and instance.miner.block < 1) or \
#                        (instance.miner.duration_hours > min_hours):

                instance.reset_hours()


    def print_table(self):
        VastMinerRealtimeTable(self.instances).print_table()


    def is_high_performance_instance(self, inst: VastInstance):
        return inst.miner.block_cost() < 0.27


    def get_difficulty(self):
        if len(self.instances) == 0:
            return 0

        for ins in self.instances:
            if ins.miner and ins.miner.difficulty > 0:
                return ins.miner.difficulty

        return 0

