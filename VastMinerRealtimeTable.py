
from datetime import timedelta
from prettytable.colortable import *
from VastInstance import VastInstance
import XenBlocksCache as Cache
from Field import Field
from MinerStatistics import *
from constants import *

import config


class VastMinerRealtimeTable:

    def __init__(self, instances: list[VastInstance]):
        self.instances: list[VastInstance] = instances
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
        self.tot_gpus: float = 0
        self.tot_active_gpus: float = 0


    def total_block_per_day(self) -> float:
        return 24 * self.tot_block_rate

    def len(self) -> int:
        return len(self.instances)


    def get_instance(self, id: int) -> VastInstance:
        for inst in self.instances:
            if inst.id == id:
                return inst
        return None


    def get_instances_for_address(self, addr: str) -> list:
        filtered_list = list(filter(lambda x: x.addr and x.addr.lower() == addr.lower(), self.instances))
        return filtered_list

    def sort_on_hashrate_per_dollar(self):
        addNums = lambda x: x.miner.hashrate_per_dollar() if x.miner else 0.0
#        self.instances = sorted(self.instances, key=lambda inst: (inst.hashrate_per_dollar2()))
        self.instances = sorted(self.instances, key=addNums, reverse=True)

    def sort_on_cost(self):
        self.instances = sorted(self.instances, key=lambda inst: (inst.block_cost()))

    def get_id_for_row(self, row_nr) -> int:
        return self.instances[row_nr - 1].id


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
                if instance.miner.block_cost() > 0.5 or\
                    (instance.miner.duration_hours > 10 and instance.miner.block < 1) or \
                        instance.miner.duration_hours > min_hours:

                    instance.reset_hours()


    # Add Miner total stats
    def add_miner_stats(self, ins: VastInstance):
        if ins.is_miner_data_loaded():
            stats = ins.miner
            self.tot_hashrate += stats.hashrate
            self.tot_block += stats.block
            self.tot_super += stats.sup
            self.tot_XUNI += stats.xuni
            self.tot_block_rate += stats.block_rate()


    def print_table(self):
        table: ColorTable = ColorTable(theme=THEME1)
        h = ["#", "Vast ID", "GPUs", "Cost/h", "DFlop", "DFlop Min", "Ov", "Hash", "Hash/$", "Hours", "BLK/h", "BLK $", "BLK/d", "BLK", "SUP", "XUNI", "Since", "Location", "Status", "Addr"]
        table.field_names = h
        table.align = "r"
        table.float_format = ".2"

        total = MinerStatistics("Total Stats", 0, 0, 0, 0.0, 0.0)
        self.tot_hashrate = 0
        self.tot_cost = 0
        self.tot_block = 0
        self.tot_super = 0
        self.tot_XUNI = 0
        self.tot_block_rate = 0
        self.tot_block_cost = 0

        idx = 1
        for ins in self.instances:
            color = C_ERROR
            rental_since = self.get_rented_since(ins)

            #   Miner totals stats for all instances
            if ins.is_managed and ins.is_running():
                self.tot_cost += ins.cost_per_hour
                self.add_miner_stats(ins)

            if ins.is_managed:
                self.tot_gpus += ins.num_gpus
                if ins.is_running():
                    self.tot_active_gpus += ins.num_gpus

#                total.cost_per_hour += ins.cost_per_hour
                # Miner total stats
#                total.hashrate += stats.hashrate
#                total.block += stats.block
#                total.sup += stats.sup
#                total.xuni += stats.xuni

            # If miner stats are available...
            if ins.is_miner_data_loaded() or ins.is_manual_override():
                row = self.get_row(idx, rental_since, ins)
                color = self.get_row_color(ins)

            # No miner stats...
            else:
                color = GRAY
                row = self.get_row_for_reserved_instance(idx, rental_since, ins)

                if ins.is_running() and config.MANUAL_MODE is True:
                    color = C_OK

                elif ins.is_running():
                    color = C_WARNING

                elif not ins.is_running() and not ins.is_outbid():
                    color = C_ATTENTION_BLINK

            self.add_row(table, row, color)
            idx += 1

        table.add_row(["-"*len(header) for header in h])

        # Totals row
        self.tot_hashrate_per_dollar = self.tot_hashrate / self.tot_cost if self.tot_cost > 0 else 0
        print()
        self.tot_block_cost = self.tot_cost / self.tot_block_rate if self.tot_block_rate > 0 else 0
#        self.tot_block_cost1 = total.cost_per_hour / total.block_rate()
        row = self.get_totals_row()
        self.add_row(table, row, GOLD)

        print(table)
        time = self.snapshot_time.strftime('%Y-%m-%d %H:%M')
        print()
        f = Field(GOLD)
        print("  ", f.gray(time), "   Diff: ", f.yellow(str(int(self.get_difficulty()/1000))+"K"))


    def verify_difficulty(self, diff: int):

        for inst in self.instances:
            if inst.is_running() and inst.miner:
                if diff != inst.miner.difficulty:
                    raise Exception(">>>>>>  WTF!!!")


    def add_row(self, table: ColorTable, row: list, color: str):
        justified_row: list = self.justify_row(row)
        formatted_row: list = []
        field = Field(color)

        for text in justified_row:
            formatted_row.append(field.format(text))

        table.add_row(formatted_row)


    def get_row(self, row_nr: int, rental_since: str, ins: VastInstance) -> list:
        supers = str(ins.miner.sup) if ins.miner.sup > 0 else ""
        addr = ins.addr[0:6] + "..." if ins.addr else "-"
        link = f"http://" + ins.get_host() if ins.get_host() else "N/A"
        override = "X" if ins.is_manual_override() else ""
        miner_status = ins.miner_status[0:2]
        hpd = f"{ins.miner.hashrate_per_dollar():.0f}" if ins.miner.hashrate_per_dollar() > 0 else ins.last_active.strftime('%m-%d %H:%M')

        return [
            str(row_nr),
            str(ins.id),
            str(ins.num_gpus) + " " + str(ins.gpu_name_short),
            f"${ins.cost_per_hour:.3f}",
            f"{ins.flops_per_dphtotal:.0f}",
            # 5
            f"{ins.dflop_for_min_bid():.0f}",
            # Miner data
            override,
            str(ins.miner.hashrate),
            hpd,
            str(round(ins.miner.duration_hours, 2)),
            # 10
            str(round(ins.miner.block_rate(), 2)),
            f"${ins.miner.block_cost():.3f}",
            f"{ins.miner.blocks_per_day():.1f}",          # 7
            str(ins.miner.block),          # 7
            supers,
            # 15
            str(ins.miner.xuni),
            # Other
            rental_since,
#            f.format(link),
            ins.geolocation[0:11],
            ins.actual_status,
            addr
        ]

    def justify_row(self, row: list):
        return [
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            # 5
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],
            # 10
            row[10],
            row[11],
            row[12],
            row[13],
            row[14],
            # 15
            row[15],
            row[16],
            row[17],
            row[18],
            row[19],
            # 20
        ]



    def get_row_for_reserved_instance(self, row_nr: int, rental_since: str, inst: VastInstance) -> list:

        addr = inst.addr[0:6] + "*" if inst.addr else "-"
        link = f"http://" + inst.get_host() if inst.get_host() else "N/A"
        hpd = inst.last_active.strftime('%m-%d %H:%M') if inst.last_active else "-"
        return [
            str(row_nr),
            str(inst.id),
            str(inst.num_gpus) + " " + str(inst.gpu_name_short),
            f"${inst.cost_per_hour:.3f}",
            f"{inst.flops_per_dphtotal:.0f}",
            f"{inst.dflop_for_min_bid():.0f}",
            #  Miner data
            "-",
            "-",
            hpd,
            "-",
#            str(round(inst.get_age_in_hours(), 1)),
            "-",
            "-",
            "-",  # 7
            "-",  # 7
            "-",
            "-",
            # Other
            rental_since,
#            f.format(link),
            inst.geolocation[0:11],
            inst.actual_status,
            addr
        ]

    def get_totals_row(self) -> list:
        return [
            # Vast instance
            "",
            "Totals",
            f"{self.tot_active_gpus}",
            f"${self.tot_cost:.2f}",
            "",
            "",
            "",
            # Miner stats
            f"{self.tot_hashrate}",
            f"{self.tot_hashrate_per_dollar:.0f}",
            "",
            f"{self.tot_block_rate:.1f}",
            f"${self.tot_block_cost:.3f}",
            f"{self.total_block_per_day():.1f}",
            f"{self.tot_block}",
            f"{self.tot_super}",
            f"{self.tot_XUNI}",
            # Other
            "",
            "",
            "",
            ""
        ]


    def get_rented_since(self, ins: VastInstance) -> str:
        if not ins.start_date:
            return "N/A"

        start_time: datetime = datetime.fromtimestamp(ins.start_date)
        tdelta: timedelta = datetime.now() - start_time
        time_parts: tuple = Time.time_parts(tdelta)
        days = time_parts[0]
        hours = time_parts[1]

        return str(24*days + hours)
#        return str(round(Time(ins.start_date).get_age_in_hours(0), 1))


    def is_high_performance_instance(self, inst: VastInstance) -> bool:
        return inst.miner.block_cost() < 0.27


    def get_difficulty(self) -> int:
        diff = Cache.get_difficulty()
        return diff if diff else 0


    def get_row_color(self, ins: VastInstance):
        if ins.is_miner_online() and ins.miner.hashrate < 1.0:
            # Miner not started!
            # Reboot!!!
#            raise Exception("Instance needs Reboot!!! Miner is not started")
            return C_ATTENTION_BLINK

        elif ins.actual_status != "running":
            # Instance has stopped - do something!
            return C_ERROR

        elif ins.is_managed and not ins.is_miner_online():
            return C_HIGH_ALERT

        elif not ins.is_miner_online():
            return C_ATTENTION

        elif ins.is_miner_online() and ins.miner.block <= 0:
            return C_ATTENTION

        elif ins.is_managed and ins.actual_status == "running":
            color = self.hashrate_dollar_color(ins.miner.hashrate_per_dollar())
            return color if self.is_high_performance_instance(ins) else C_ATTENTION

        elif ins.actual_status == "running":
            return C_ATTENTION

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

