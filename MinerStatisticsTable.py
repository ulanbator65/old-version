
from datetime import datetime
from prettytable.colortable import *

from VastClient import VastClient
from VastInstance import VastInstance
from MinerStatistics import MinerStatistics
from MinerStatisticsHistoryRepo import MinerStatisticsHistoryRepo
from MinerGroup import MinerGroup
from Field import Field
import XenBlocksCache as Cache
from Time import Time

from constants import *

import config
import ui


class MinerStatisticsTable:

    def __init__(self, vast: VastClient):

        self.vast_instances = vast.get_instances()
        self.db = MinerStatisticsHistoryRepo()
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
        self.miner_groups: list[MinerGroup] = []


    def load_miners(self):
        addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                           "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                           "0xd9007A12b33b699Ee01B7D6f9D9fEae42AB5145C".lower(),
                           "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()]

#        addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower()]

        rank200: MinerStatistics = Cache.get_miner_stats_for_rank(200)

        print(ui.text_color("Rank 200: ", LIGHT_PINK), ui.text_color(str(rank200), LIGHT_PINK))

#        self.db.get()

        print(">>>>>>>>>>>>>>>>>")
        miner_groups = []
        for addr in addr_list:
            group = self.create_miner_group(addr)
            miner_groups.append(group)

        print(">>>>>>>>>>>>>>>>>")
        self.miner_groups = miner_groups


    def create_miner_group(self, addr: str) -> MinerGroup:
        vast_instances = self.get_instances_for_address(addr)

        miner_group: MinerGroup = MinerGroup(addr, vast_instances)
        miner_group.stats.cost_per_hour = self.calculate_total_cost(addr)
#        print(miner_group.stats)

        old_snapshot = self.select_snapshot_from_history(miner_group.id, 1)
        if old_snapshot:
            miner_group.subtract(old_snapshot)

        return miner_group


    def select_snapshot_from_history(self, id: str, min_hours: int) -> MinerStatistics:
        now = Time.now()
        history: list[tuple] = self.db.get(id)

#        print(f"Hist size: {len(history)}")

        if len(history) == 0:
            return None

        for snapshot in history:
            print(snapshot)

        for snapshot in history:
            tdelta = now.timedelta_from(snapshot[1])
            timeparts = Time.time_parts(tdelta)
            hours = timeparts[1]
            if hours >= min_hours:
                return self.db.map_row(snapshot)

        return self.db.map_row(history[len(history) - 1])


    def print(self):
#        test = MinerStatistics.create_with_timestamp("Kalle", 1, 33,44,55, 99.88)
#        self.db.create("Kalle", test)
#        result = self.db.get("Kalle", 99)
#        print(result[0])

        self.load_miners()
        self.save_miner_stats()
        self.print_table()


    def save_miner_stats(self):

        for mg in self.miner_groups:
            stats: MinerStatistics = mg.stats

            # Save to DB once per hour at the most
            stats2 = self.db.get_latest_version(mg.id)
            if stats2:
                diff_seconds = (stats.timestamp_s - stats2.timestamp_s)
                diff = diff_seconds / 3600
                print(diff)

                if diff > 0.99:
                    self.db.create(mg.id, stats)
                    print(f"Saved to DB: {stats}")
            else:
                self.db.create(mg.id, stats)


    def calculate_total_cost(self, address: str) -> float:
        uptime_percentage = 0.07
        instances: list[VastInstance] = self.get_instances_for_address(address)
        cost = 0.0
        for ins in instances:
            cost += ins.effective_cost_per_hour(uptime_percentage)

        return cost


    def total_block_per_day(self) -> float:
        return 24 * self.tot_block_rate


    def refresh(self):
#        if self.should_refresh_cache():
#            self.instances = self.vast.get_instances()
#            self.snapshot_time = datetime.now()
#        else:
#            self.refresh_miner_stats()

        self.snapshot_time = datetime.now()


    def get_instances_for_address(self, addr: str) -> list[VastInstance]:
        return list(filter(lambda x: x.addr and x.addr.lower() == addr.lower(), self.vast_instances))

    def sort_on_cost(self):
        self.vast_instances = sorted(self.vast_instances, key=lambda inst: (inst.block_cost()))

    def get_id_for_row(self, row_nr) -> int:
        return self.vast_instances[row_nr - 1].id


    def get_ids_for_index(self, index: list) -> list:
        return [self.vast_instances[num - 1].id for num in index]


    def reset_hours(self):
        min_hours = 0.2
        for instance in self.vast_instances:
            if instance.miner:
                if instance.miner.block_cost() > 0.5 or\
                    (instance.miner.duration_hours > 10 and instance.miner.block < 1) or \
                        instance.miner.duration_hours > min_hours:

                    instance.reset_hours()


    def print_table(self):
        table: ColorTable = ColorTable(theme=THEME1)
        header = ["Address", "Cost/h", "Effect", "Hours", "BLK/h", "BLK cost", "BLK/d", "BLK", "SUP", "XUNI"]
        table.field_names = header
        table.align = "r"
        table.float_format = ".2"

#        total = MinerStatistics("Total", 0, 0, 0, 0.0, 0.0)
        self.tot_hashrate = 0
        self.tot_cost = 0
        self.tot_block = 0
        self.tot_super = 0
        self.tot_XUNI = 0
        self.tot_block_rate = 0
        self.tot_block_cost = 0

        idx = 1
        for mg in self.miner_groups:

            stats = mg.stats
            #
            #   Miner totals stats for all instances
            #
            self.tot_cost += stats.cost_per_hour
            # Miner total stats
            self.tot_hashrate += stats.hashrate
            self.tot_block += stats.block
            self.tot_super += stats.super
            self.tot_XUNI += stats.xuni
            self.tot_block_rate += stats.block_rate(0.1)

            #
            #   Individual miner stats
            #

            row = self.get_row(idx, mg)
            color = self.get_row_color(mg)

            self.add_row(table, row, color)
            idx += 1

        separator = self.get_row_separator(header)
        table.add_row(separator)

        # Totals row
        self.tot_hashrate_per_dollar = self.tot_hashrate / self.tot_cost if self.tot_cost > 0 else 0
        self.tot_block_cost = self.tot_cost / self.tot_block_rate if self.tot_block_rate > 0 else 0
#        self.tot_block_cost = total.cost_per_hour / total.block_rate()
        row = self.get_totals_row()
        self.add_row(table, row, GOLD)

        print()
        print(table)


    def add_row(self, table: ColorTable, row: list, color: str):
        justified_row: list = self.justify_row(row)
        formatted_row: list = []
        field = Field(color)

        for text in justified_row:
            formatted_row.append(field.format(text))

        table.add_row(formatted_row)


    def get_row(self, row_nr: int, mg: MinerGroup) -> list:
#        addr = mg.id[0:6] + "..."

        return [
            str(mg.id[0:8]+"..."),
            f"${mg.stats.cost_per_hour:.3f}",
            f"{int(mg.effect()*100):} %",
            str(round(mg.stats.duration_hours, 1)),
            str(round(mg.stats.block_rate(0.1), 2)),
            # 5
            f"${mg.stats.block_cost():.3f}",
            f"{mg.stats.blocks_per_day(default=0.1):.1f}",          # 7
            str(mg.stats.block),          # 7
            str(mg.stats.super),             # 15
            str(mg.stats.xuni)
            # 10
        ]


    def get_totals_row(self) -> list:
        return [
            # Vast instance
            "",
            f"${self.tot_cost:.2f}",
            "",
            "",
            f"{self.tot_block_rate:.1f}",
            # 5
            f"${self.tot_block_cost:.3f}",
            f"{self.total_block_per_day():.1f}",
            f"{self.tot_block}",
            f"{self.tot_super}",
            f"{self.tot_XUNI}",
        ]


    def get_row_separator(self, header) -> list:
        return [
            # Vast instance
            "-"*12,
            "-"*len(header[1]),
            "-"*len(header[2]),
            "-"*len(header[3]),
            "-"*len(header[4]),
            # 5
            "-"*len(header[5]),
            "-"*len(header[6]),
            "-"*len(header[7]),
            "-"*len(header[8]),
            "-"*len(header[9])
        ]


    def justify_row(self, row: list):
        return [
            row[0],
            row[1],
            row[2].rjust(6),
            row[3].rjust(5),
            row[4].rjust(5),
            # 5
            row[5].rjust(8),
            row[6].rjust(5),
            row[7].rjust(3),
            row[8].rjust(3),
            row[9].rjust(3)
            # 10
        ]


    def get_rented_since(self, ins: MinerStatistics):
        if not ins.start_date:
            return "N/A"

        start_time = datetime.fromtimestamp(ins.start_date)
        tdelta = datetime.now() - start_time

        total_min = int(tdelta.total_seconds()/60)
        day = int(total_min/24.0/60.0)
        hour = int((total_min/60) - day*24)
        min = total_min - day*24*60 - hour*60
        min = int(min)

        return str(day) + "d " + str(hour) + "h"
#        return str(day) + "d " + str(hour) + "h " + str(min) + "m"


    def is_high_performance_instance(self, inst: MinerStatistics):
        return inst.miner.block_cost() < 0.27


    def get_row_color(self, ins: MinerGroup):
        return C_OK


    def hashrate_dollar_color(self, hashrate_per_dollar) -> str:
        top_rate = 18000
        mid_rate = 5000
        if hashrate_per_dollar == 'Error' or hashrate_per_dollar <= mid_rate:
            return C_ERROR
        elif hashrate_per_dollar < top_rate:
            return C_WARNING
        elif hashrate_per_dollar >= top_rate:
            return C_OK
        else:
            return GRAY


