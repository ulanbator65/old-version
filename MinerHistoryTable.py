
from datetime import datetime
from prettytable.colortable import *

from VastClient import VastClient
from VastInstance import VastInstance
from MinerStatistics import MinerStatistics
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from MinerGroup import MinerGroup
from Balance import Balance
from Field import Field
import XenBlocksCache as Cache
from XenBlocksWallet import XenBlocksWallet
from Time import Time

from ui import *

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
#                   "0xd9007A12b33b699Ee01B7D6f9D9fEae42AB5145C".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]


class MinerHistoryTable:

    def __init__(self, vast: VastClient):

        self.vast = vast
        self.vast_balance: Balance = None
        self.vast_instances = None
        self.db = XenBlocksWalletHistoryRepo()
        self.snapshot_time: datetime = datetime.now()
        # Statistics
        self.tot_hashrate = 0
        self.tot_hashrate_per_dollar = 0
        self.tot_gpus = 0
        self.tot_cost: float = 0
        self.tot_block: int = 0
        self.tot_super: int = 0
        self.tot_XUNI: int = 0
        self.tot_block_rate1: float = 0
        self.tot_block_rate2: float = 0
        self.tot_block_per_day: float = 0
        self.tot_block_cost: float = 0
        self.tot_block_cost_3h: float = 0
        self.all_blocks = 0
        self.miner_groups: list[MinerGroup] = []


    def load_miners(self):
        self.vast_instances = self.vast.get_instances()

#        addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower()]
#        addr_list: list = ["0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower()]
#        addr_list = ["0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()]

        now = int(Time.now().timestamp)
        miner_groups = []

        for addr in addr_list:
            group = self.create_miner_group(addr, now)
            if group:
                miner_groups.append(group)

        self.miner_groups = miner_groups
        self.sort_on_cost()


    def map(self, w: XenBlocksWallet) -> MinerStatistics:
        return MinerStatistics(w.addr, w.block, w.sup, w.xuni, 0, 0)


    def create_miner_group(self, addr: str, timestamp_s: int) -> MinerGroup:
        balance_usd: float = self.vast.get_vast_balance()
        print("Balance>>>", balance_usd)

        vast_instances = self.get_instances_for_address(addr)

        balance = Cache.get_wallet_balance(addr, timestamp_s)
        if balance:
            self.save_historic_data(balance)

            timestamp_s = Time.now().subtract_hours(25).timestamp
            balance_history = self.db.get_history(addr, int(timestamp_s))

            return MinerGroup(balance, balance_history, vast_instances)

        return MinerGroup(balance, None, vast_instances)


    def select_snapshot_from_history(self, history: list[XenBlocksWallet], age_hours: int) -> XenBlocksWallet:

        timestamp_s = Time.now().subtract_hours(age_hours).timestamp

        for h in history:
            print(datetime.fromtimestamp(h.timestamp_s))
            if h.timestamp_s < timestamp_s:
                return h

        return None


    def print(self):
        self.load_miners()
#        self.save_miner_stats()
        self.print_table()


    def update_balance_history(self, timestamp_s: int):
        for addr in addr_list:
            balance = Cache.get_wallet_balance(addr, timestamp_s)
            if balance:
                self.save_historic_data(balance)


    def save_historic_data(self, snapshot: XenBlocksWallet, min_diff_minutes: int = 20) -> bool:

        balance_usd: float = self.vast.get_vast_balance()
        print("Balance>>>", balance_usd)

        # Save to DB once per hour at the most
        latest_snapshot = self.db.get_latest_version(snapshot.addr)

        if latest_snapshot:
            diff_seconds = (snapshot.timestamp_s - latest_snapshot.timestamp_s)
            diff_minutes = diff_seconds / 60
            print("Diff in minutes: " + str(int(diff_minutes)))

            if diff_minutes > min_diff_minutes:
                self.db.create(snapshot)
                print(ORANGE + f"Saved to DB: {snapshot.to_str()}" + RESET)
                return True
        else:
            self.db.create(snapshot)
            return True

        return False


    def _block_rate(self, mg: MinerGroup, hours: int) -> float:
        snapshot = mg.select_snapshot_from_history(hours)

        if not mg.balance or not snapshot:
            return 0.0

        delta_balance = mg.balance.difference(snapshot)

        tdelta = delta_balance.timestamp_s
        tdelta = tdelta/3600
        print("Hours: ", hours)
        print("TDelta: ", tdelta)
        print("mg: ", delta_balance.block)
        print("snap: ", delta_balance.block)
        block_delta = delta_balance.block
        xuni_delta = delta_balance.xuni

        return block_delta / tdelta


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
        self.miner_groups = sorted(self.miner_groups, key=lambda x: x.cost_ph, reverse=True)

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
        delta_hours1 = 1.2
        delta_hours2 = 3.0
        table: ColorTable = ColorTable(theme=THEME1)
        header = ["Address", "GPUs", "Cost/h", "Effect", "Hours", "BLK/h", "$/BLK", "$/BLK/3h", "BLK/3h", "BLK/d", "BLK", "SUP", "XUNI", "Total"]
        table.field_names = header
        table.align = "r"
        table.float_format = ".2"

        self.tot_gpus = 0
        self.tot_cost = 0
        self.tot_block = 0
        self.tot_super = 0
        self.tot_XUNI = 0
        self.tot_block_rate1 = 0
        self.tot_block_rate2 = 0
        self.tot_block_cost = 0
        self.all_blocks = 0

        idx = 1
        for mg in self.miner_groups:
            delta_1: XenBlocksWallet = mg.get_delta(delta_hours1)
            delta_2: XenBlocksWallet = mg.get_delta(delta_hours2)

            row = self.get_row(idx, mg, delta_1, delta_2)

            if delta_1:
                self.tot_block += delta_1.block
                self.tot_super += delta_1.sup
                self.tot_XUNI += delta_1.xuni
                self.tot_block_rate1 += delta_1.block / (delta_1.timestamp_s / 3600)

            self.tot_gpus += mg.active_gpus
            self.tot_cost += mg.cost_ph
            self.all_blocks += mg.get_block_count_for_address()
            self.tot_block_per_day += mg.block_rate_per_day()
#            self.tot_block_rate += stats.block_rate(0.1)

            color = self.get_row_color(mg, delta_1)
            self.add_row(table, row, color)
            idx += 1

        separator = self.get_row_separator(header)
        table.add_row(separator)

        # Totals row
        self.tot_hashrate_per_dollar = self.tot_hashrate / self.tot_cost if self.tot_cost > 0 else 0
        self.tot_block_cost = self.tot_cost / self.tot_block_rate1 if self.tot_block_rate1 > 0 else 0
        self.tot_block_cost_3h = self.tot_cost / self.tot_block_rate2 if self.tot_block_rate2 > 0 else 0
#        self.tot_block_cost = total.cost_per_hour / total.block_rate()
        row = self.get_totals_row()
        self.add_row(table, row, GOLD)

        print()
        print(table)
        time = datetime.now().strftime('%Y-%m-%d %H:%M')
        difficulty = Cache.get_difficulty()
        print()
        f = Field(GOLD)
        print("  ", f.gray(time), "   Diff: ", f.yellow(str(int(difficulty/1000))+"K"))


    def add_row(self, table: ColorTable, row: list, color: str):
        justified_row: list = self.justify_row(row)
        formatted_row: list = []
        field = Field(color)

        for text in justified_row:
            formatted_row.append(field.format(text))

        table.add_row(formatted_row)


    def get_row(self, row_nr: int, mg, delta_1: XenBlocksWallet, delta_2: XenBlocksWallet) -> list:
        if delta_1:
            delta_1.cost_per_hour = mg.cost_ph
            block_rate1 = delta_1.block_rate()
            block_cost = delta_1.block_cost()
#            block_cost = mg.cost_ph / block_rate1 if block_rate1 > 0 else 0.0
            block_rate2 = delta_2.block_rate()
            block_cost_2 = mg.cost_ph / block_rate2 if block_rate2 > 0 else 0.0
            block_per_day = mg.block_rate_per_day()

            return [
                str(mg.id[0:8]+"..."),
                f"{mg.active_gpus}",
                f"${mg.cost_ph:.3f}",
                f"{int(mg.effect()*100):} %",
                f"{delta_1.duration_hours():.1f}",
                # 5
                to_string(block_rate1),
                f"${block_cost:.3f}",
                f"${block_cost_2:.3f}",
                to_string(block_rate2),
                to_string(block_per_day),
                # 10
                str(delta_1.block),          # 7
                str(delta_1.sup),             # 15
                str(delta_1.xuni),
                str(mg.get_block_count_for_address())
            ]
        else:
            return [
                str(mg.id[0:8]+"..."),
                f"{mg.active_gpus}",
                f"${mg.cost_ph:.3f}",
                f"{int(mg.effect()*100):} %",
                "",
                # 5
                "",
                "",
                "",
                "",
                "",
                # 10
                "",
                "",
                "",
                str(mg.get_block_count_for_address())
            ]


    def get_totals_row(self) -> list:
        return [
            # Vast instance
            "",
            f"{self.tot_gpus}",
            f"${self.tot_cost:.2f}",
            "",
            "",
            # 5
            f"{self.tot_block_rate1:.1f}",
            f"${self.tot_block_cost:.3f}",
            f"${self.tot_block_cost_3h:.3f}",
            f"{self.tot_block_rate2:.1f}",
            f"{self.tot_block_per_day:.0f}",
            # 10
            f"{self.tot_block}",
            f"{self.tot_super}",
            f"{self.tot_XUNI}",
            f"{self.all_blocks}",
        ]


    def get_row_separator(self, header) -> list:
        return [
            # Vast instance
            "-"*11,
            "-"*len(header[1]),
            "-"*len(header[2]),
            "-"*len(header[3]),
            "-"*len(header[4]),
            # 5
            "-"*len(header[5]),
            "-"*len(header[6]),
            "-"*len(header[7]),
            "-"*len(header[8]),
            "-"*len(header[9]),
            # 10
            "-"*len(header[10]),
            "-"*len(header[11]),
            "-"*len(header[12]),
            "-"*len(header[13])
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
            row[7],
            row[8].rjust(3),
            row[9],
            # 10
            row[10],
            row[11],
            row[12],
            row[13],
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


    def get_row_color(self, mg: MinerGroup, delta: XenBlocksWallet):

        if mg.active_gpus == 0 and mg.block_rate_per_hour(1) < 0.01:
            return GRAY

        elif mg.active_gpus == 0 or mg.get_block_count_for_address() == 0:
            return C_ATTENTION

        elif mg.active_gpus > 0 and delta and delta.block == 0:
            return C_ATTENTION

        elif mg.active_gpus > 0 and delta and delta.block_cost() > 0.12:
            return C_ATTENTION

#        elif mg.block_rate_per_hour(1) < 1.0:
#            return ORANGE

        return C_OK


def to_string(value: float) -> str:
    if value < 0.01:
        return "-"
    return f"{value:.2f}"

