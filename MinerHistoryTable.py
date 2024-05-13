
from datetime import datetime, timedelta
from prettytable.colortable import *

from VastClient import VastClient
from VastInstance import VastInstance
from MinerStatistics import MinerStatistics
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from db.HistoryManager import HistoryManager
from MinerGroup import MinerGroup
from Balance import Balance
from Field import Field
import XenBlocksCache as Cache
from XenBlocksWallet import XenBlocksWallet
from Time import Time
from HistoricalBalances import HistoricalBalances
import constants
import logger as log

from input import *

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
        self.history = HistoryManager()
        self.db = XenBlocksWalletHistoryRepo()
        self.snapshot_time: datetime = datetime.now()
        # Statistics
        self.tot_hashrate = 0
        self.tot_hashrate_per_dollar = 0
        self.tot_gpus = 0
        self.tot_active_gpus = 0
        self.tot_cost_ph: float = 0
        self.actual_cost_ph: float = 0
        self.tot_block: int = 0
        self.tot_block2: int = 0
        self.tot_super: int = 0
        self.tot_XUNI: int = 0
        self.tot_block_rate1: float = 0
        self.tot_block_rate2: float = 0
        self.tot_block_per_day: float = 0
        self.tot_block_cost1: float = 0
        self.tot_block_cost2: float = 0
        self.tot_block_cost_d: float = 0
        self.average_dflop: int = 0
        self.all_blocks = 0
        self.miner_groups: list[MinerGroup] = []


    def load_miner_groups(self):
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

        vast_instances = self.get_instances_for_address(addr)
        balance = Cache.get_wallet_balance(addr, timestamp_s)

        return MinerGroup(balance, vast_instances)


    def print(self):
        self.load_miner_groups()
        self.print_table()


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



    def print_table(self):
        delta_hours1 = 0.7
        delta_hours2 = 4.0
        table: ColorTable = ColorTable(theme=THEME1)
        header = ["Address", "GPUs", "Cost", "USD/h", "DFLOP", "Effect", "Hours", "BLK/h", "BLK/3h", "BLK/d", "$/BLK", "$/BLK/3h", "$/BLK/d", "BLK", "SUP", "XUNI", "Total"]
        table.field_names = self.highlight_columns(header)
        table.align = "r"
        table.float_format = ".2"

        self.reset_data()
        now = int(datetime.now().timestamp())

        historic_balances1 = get_balances(now, delta_hours1, delta_hours1 + 0.8)
        historic_balances2 = get_balances(now, delta_hours2, delta_hours2 - 1)
        historic_balances_day = get_balances(now, 24, 22)

        vast_balance: float = self.vast.get_vast_balance()
        idx = 1
        for mg in self.miner_groups:

            delta_1: XenBlocksWallet = None
            if historic_balances1:
                delta_1: XenBlocksWallet = mg.balance.difference(historic_balances1.get_for_addr(mg.id))

            delta_2: XenBlocksWallet = None # mg.get_delta_new(now, delta_hours2)
            if historic_balances2:
                delta_2 = mg.balance.difference(historic_balances2.get_for_addr(mg.id))

            delta_day: XenBlocksWallet = None # mg.get_delta_new(now, 24)
            if historic_balances_day:
                delta_day = mg.balance.difference(historic_balances_day.get_for_addr(mg.id))

            row = self.get_row(idx, mg, delta_1, delta_2, delta_day)

            self.tot_super += get_superblocks(mg.id, historic_balances1, historic_balances2 , historic_balances_day)

            if delta_1:
                self.tot_block += delta_1.block
                self.tot_XUNI += delta_1.xuni
                self.tot_block_rate1 += delta_1.block / (delta_1.timestamp_s / 3600)

            if delta_2:
                self.tot_block2 += delta_2.block
                self.tot_block_rate2 += delta_2.block / (delta_2.timestamp_s / 3600)

            if delta_day:
                self.tot_block_per_day += delta_day.block

            self.tot_active_gpus += mg.active_gpus
            self.tot_cost_ph += mg.cost_ph
            self.all_blocks += mg.get_block_count_for_address()
            self.average_dflop += mg.dflop

#            self.tot_block_rate += stats.block_rate(0.1)

            color = self.get_row_color(mg, delta_1)
            self.add_row(table, row, color)
            idx += 1

        separator = self.get_row_separator(header)
        table.add_row(separator)

        # Totals row
        if historic_balances1:
            actual_cost = (historic_balances1.vast_balance - vast_balance)
            hours = (now - historic_balances1.timestamp) / 3600
            self.actual_cost_ph = actual_cost / hours
            self.tot_block_cost1 = actual_cost / self.tot_block if self.tot_block > 0 else 0

        if historic_balances2:
            actual_cost = (historic_balances2.vast_balance - vast_balance)
#            hours = (now - historic_balances2.timestamp) / 3600
            self.tot_block_cost2 = actual_cost / self.tot_block2 if self.tot_block2 > 0 else 0

        if historic_balances_day:
            actual_cost = (historic_balances_day.vast_balance - vast_balance)
#            print(DARK_PINK, "Delta Time:  ",  str(round(hours, 1)))
            print(DARK_PINK, "Delta USD:   ",  round(actual_cost, 1))
            print(DARK_PINK, "Delta Block: ",  self.tot_block_per_day)
            self.tot_block_cost_d = actual_cost / self.tot_block_per_day if self.tot_block_per_day > 0 else 0

        self.tot_hashrate_per_dollar = self.tot_hashrate / self.tot_cost_ph if self.tot_cost_ph > 0 else 0

        row = self.get_totals_row()
        self.add_row(table, row, GOLD)

        print()
        print(table)
        self.print_footer()


    def print_footer(self):
        now = datetime.now().strftime('%H:%M:%S')
        difficulty = Cache.get_difficulty()
        print()
        f = Field(GOLD)
        print("  ", f.gray(now), "   Diff: ", f.yellow(str(int(difficulty/1000))+"K"))

        t0 = int(datetime.now().timestamp())
        tot_balance = 0
        for a in constants.ALL_ADDR:
            balance = Cache.get_wallet_balance(a, t0)
            tot_balance += balance.block

            # Super blocks are reported inaccurately, sometimes as 0 - so remove from count
        #            tot_balance -= balance.sup
        #            print(balance.block)

        log.warning(ORANGE + f"    Total balance: {tot_balance}")


    def add_row(self, table: ColorTable, row: list, color: str):
        justified_row: list = self.justify_row(row)
        formatted_row: list = []
        field = Field(color)

        for text in justified_row:
            formatted_row.append(field.format(text))

        table.add_row(formatted_row)


    def get_row(self,
                row_nr: int,
                mg,
                delta_1: XenBlocksWallet,
                delta_2: XenBlocksWallet,
                delta_day: XenBlocksWallet) -> list:

        if delta_1:
            delta_1.cost_per_hour = mg.cost_ph
            block_rate1 = delta_1.block_rate()
            block_cost = delta_1.block_cost()

            block_rate2 = delta_2.block_rate() if delta_2 else 0.0
            block_cost_2 = mg.cost_ph / block_rate2 if block_rate2 > 0 else 0.0

            block_per_day = delta_day.block if delta_day else 0
            block_cost_day = mg.cost_ph / block_per_day if block_per_day > 0 else 0.0

            return [
                str(mg.id[0:8]+"..."),
                f"{mg.active_gpus}/{mg.total_gpus}",
                f"${mg.cost_ph:.3f}",
                "",
                f"{mg.dflop:.0f}",
                # 5
                f"{int(calc_effect(mg.active_gpus, delta_1.block)):} %",
                f"{delta_1.duration_hours():.1f}",
                to_string(block_rate1),
                to_string(block_rate2),
                to_string(block_per_day),
                # 10
                block_cost_to_string(block_cost),
                block_cost_to_string(block_cost_2),
                "",
                str(delta_1.block),          # 7
                str(delta_1.sup),             # 15
                str(delta_1.xuni),
                str(mg.get_block_count_for_address())
            ]
        else:
            return [
                str(mg.id[0:8]+"..."),
                f"{mg.active_gpus}/{mg.total_gpus}",
                f"${mg.cost_ph:.3f}",
                "",
                f"{mg.dflop:.0f}",
                # 5
                f"{int(calc_effect(mg.active_gpus, 0)):} %",
                "",
                "",
                "",
                "",
                # 10
                "",
                "",
                "",
                "",
                "",
                "",
                str(mg.get_block_count_for_address())
            ]


    def get_totals_row(self) -> list:
#        effect = (self.tot_block / self.tot_active_gpus) * 100 if self.tot_active_gpus > 0 else 0
        effect = calc_effect(self.tot_active_gpus, self.tot_block)
        return [
            # Vast instance
            "",
            f"{self.tot_active_gpus}",
            f"${self.tot_cost_ph:.2f}",
            f"${self.actual_cost_ph:.2f}",
            f"{int(self.average_dflop/2)}",
            # 5
            f"{int(effect)} %",
            "",
            f"{self.tot_block_rate1:.1f}",
            to_string(self.tot_block_rate2),
            f"{self.tot_block_per_day}",
            # 10
            f"${self.tot_block_cost1:.3f}",
            block_cost_to_string(self.tot_block_cost2),
            block_cost_to_string(self.tot_block_cost_d),
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
            "-"*len(header[13]),
            "-"*len(header[14]),
            "-"*len(header[15]),
            "-"*len(header[16])
        ]


    def highlight_columns(self, header: list) -> list:
        col1 = 7
        col2 = 10
        new_header = header.copy()
        new_header[col1] = GOLD + new_header[col1]
        new_header[col2] = GOLD + new_header[col2]

        return new_header


    def justify_row(self, row: list):
        return row


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

        if mg.active_gpus == 0:
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


    def reset_data(self):
        self.tot_hashrate = 0
        self.tot_hashrate_per_dollar = 0
        self.tot_gpus = 0
        self.tot_active_gpus = 0
        self.tot_cost_ph: float = 0
        self.actual_cost_ph: float = 0
        self.tot_block: int = 0
        self.tot_block2: int = 0
        self.tot_super: int = 0
        self.tot_XUNI: int = 0
        self.tot_block_rate1: float = 0
        self.tot_block_rate2: float = 0
        self.tot_block_per_day: float = 0
        self.tot_block_cost1: float = 0
        self.tot_block_cost2: float = 0
        self.tot_block_cost_d: float = 0
        self.average_dflop: int = 0
        self.all_blocks = 0


def get_balances(now: float, age_in_hours: float, fallback_age: float) -> HistoricalBalances:
    t0 = datetime.fromtimestamp(now)
    t1 = t0 - timedelta(minutes=age_in_hours*60)
    t_fallback = t0 - timedelta(minutes=fallback_age*60)

#    print("T0: ", str(int(t0.timestamp())))
#    print("T1: ", str(int(t1.timestamp())))
#    print("Fallback: ", str(int(fallback.timestamp())))

    return HistoryManager().get_balances_with_fallback(int(t1.timestamp()), int(t_fallback.timestamp()))


def get_superblocks(addr: str,
                    balances_1: HistoricalBalances,
                    balances_2: HistoricalBalances,
                    balances_3: HistoricalBalances) -> int:

    if balances_3 and balances_3.get_for_addr(addr):
        return balances_3.get_for_addr(addr).sup

    if balances_2 and balances_2.get_for_addr(addr):
        return balances_2.get_for_addr(addr).sup

    if balances_1 and balances_1.get_for_addr(addr):
        return balances_1.get_for_addr(addr).sup

    return 0


def duration_hours(t1, t2):
    return (t1 - t2) / 3600


def to_string(value: float) -> str:
    if value < 0.01:
        return "-"
    return f"{value:.2f}"


def block_cost_to_string(value: float):
    if value < 0.01:
        return "-"
    return f"${value:.3f}"


#
#      Effect calculationn based on how many blocks each gpu produces per hour
#
def calc_effect(gpus: int, block: int) -> float:
    if gpus == 0:
        return 0.0

    #  One gpu is estimated to produce x nr of blocks per hour,
    #  which equals the effect of 100 %
    #  Example: 0.8 block per gpu at difficulty 90K
    estimated_block_per_gpu = 0.8

    block_per_gpu = (100 * block / (gpus * estimated_block_per_gpu))
    return block_per_gpu
