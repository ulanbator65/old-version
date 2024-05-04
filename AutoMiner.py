
import time

from Automation import Automation
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from Menu import Menu
from VastMinerTable import VastMinerTable
import logger


f = Field(ORANGE)
fgray = Field(GRAY)

S_START_MINING = "XUNI Miner running..."
S_MANAGE_MINERS = "Setup miners for XUNI..."



class AutoMiner:

    def __init__(self, vast):
        self.vast: VastClient = vast
        self.automation = Automation(vast)
        self.hours = 0
        self.minutes: int = 0
        self.state: str = "None"



    def mine_xuni(self):
        dflop_min = 215

        self.set_state(S_START_MINING, [f"DFLOP min: {dflop_min}",
                                        f"GPU models: A40, A5000",
                                        "",
                                        "Mining Start: " + str(self.mining_start)[11:19],
                                        "Mining End:   " + str(self.mining_end)[11:19]])
        while True:
            now = self.controller.get_time()
            #
            #  Mine at the top of the hour when XUNI's are produced
            #
            if now.timestamp() > self.mining_start.timestamp():
                self.state_startup_miners(dflop_min)

                # Begin next iteration
                self.reset()
                self.set_state(S_START_MINING, [f"DFLOP min: {dflop_min}",
                                                f"GPU models: A40, A5000",
                                                "",
                                                "Mining Start: " + str(self.mining_start)[11:19],
                                                "Mining End:   " + str(self.mining_end)[11:19]])

            hash_per_usd_min: int = 15000
            instances = self.get_vast_instances()
            self.reboot_instances(instances, hash_per_usd_min)

            self.buy_cheap_a5000(500)
            time.sleep(2*60)


    def state_manage_started_miners(self):
        self.set_state(S_MANAGE_MINERS,
                       ["Passive mining at:   " + str(self.passive_mining_start)[11:19]])

        # Reset mining duration
        #        now = Time.now().timestamp
        #        diff = now - self.checkpoint1.timestamp()
        #        print("Diff: ", diff)
        #        if abs(diff) < 61:
        #            self.reset_hours(self.get_vast_instances())

        while True:
            now = self.controller.get_time()
            print("Min1: ", now.minute)
            print("Min2: ", self.checkpoint1.minute)

            instances = self.get_vast_instances()

            if now.timestamp() < self.passive_mining_start.timestamp():
                pass
            #                self.increase_bid(instances)
            else:
                break

            self.handle_startup(instances)

            logger.print_info(f"Mining ends at: {str(self.mining_end)[11:19]}")
            time.sleep(60)


    def state_just_keep_mining(self):
        # Mine until XUNI is stopped being produced
        self.set_state(S_MANAGE_MINERS,
                       ["Mining ends at:   " + str(self.mining_end)[11:19]])

        while True:
            now = self.controller.get_time()
            #            print("Min1: ", now.minute)
            #            print("Min2: ", self.checkpoint1.minute)

            # Mining ends...
            if now.timestamp() > self.mining_end.timestamp():
                self.state_kill_all_running_instances()
                break

            logger.print_info(f"Mining ends at: {str(self.mining_end)[11:19]}")
            time.sleep(1*60)
            instances = self.get_vast_instances()
            self.handle_problematic_instances(instances)
            time.sleep(1*60)


    def buy_cheap_a5000(self, dflop_min: int):
        print_attention("Buy cheap miners...")

        offers: list[VastOffer] = self.automation.offers_A5000(dflop_min)
        self.buy_miners(dflop_min, offers)
        print_attention("Done!")


    def buy_miners(self, dflop_min: int, offers: list[VastOffer]):

        if len(offers) == 0:
            print(Field.attention(f"No offers above required flops per dph found: {dflop_min}"))
        else:
            for offer in offers:
                #                        best_offer: VastOffer = offers
                # Increase bid price
                price: float = offer.min_bid
                price = price * 1.02

                if offer.flops_per_dphtotal > dflop_min:
                    print(Field.attention(f"Creating instance: {offer.id}"))
                    self.vast.create_instance(config.ADDR, offer.id, price)


    def handle_startup(self, instances: list[VastInstance]):
        print_attention("Handle problem instances...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 15000
        dflop_min: int = 300

        #        self.kill_outbid_instances(instances, dflop_min)
        self.handle_low_performing_instances(instances, hash_per_usd_min)
        self.kill_unable_to_start_instances(instances)


    def handle_problematic_instances(self, instances: list[VastInstance]):
        print_attention("Handle problem instances...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 15000
        dflop_min: int = 300

        self.kill_outbid_instances(instances, dflop_min)
        self.handle_low_performing_instances(instances, hash_per_usd_min)
        self.kill_unable_to_start_instances(instances)

        print_attention("Done!")


    def kill_outbid_instances(self, instances: list[VastInstance], dflop_limit: int):
        print_attention("Kill outbid instances...")

        for inst in instances:
            if inst.is_outbid() and (inst.flops_per_dphtotal < dflop_limit):
                print_attention(f"Stopping id={inst.id} due to: outbid")
                print(f"Inst DFLOP: {inst.flops_per_dphtotal}")
                self.vast.kill_instance(inst.id)

        print_attention("Done!")


    def reboot_instances(self, instances: list[VastInstance], hash_per_usd_min: int):
        print_attention("Reboot instances...")

        all_instances = self.vast.get_instances()
        self.vast.get_miner_data(all_instances)


        #        for inst in instances:
        for inst in all_instances:
            hpd = inst.hashrate_per_dollar()

            # Reboot if hashrate is low but not zero
            if inst.is_running() and (hpd < hash_per_usd_min):
                print_attention(f"Rebooting id={inst.id} due to: Low hashrate per USD!")
                print(f"Hashrate: {hpd}")
                self.vast.reboot_instance(inst.id)

        print_attention("Done!")


    def handle_low_performing_instances(self, instances: list[VastInstance], hash_per_usd_min: int):
        print_attention("Handle low performing instances...")

        limit_hashrate = 0

        for inst in instances:
            hpd: int = inst.hashrate_per_dollar()

            # Reboot if hashrate is low but not zero
            if inst.is_running() and (hpd >= limit_hashrate) and (hpd < hash_per_usd_min):
                print_attention(f"Rebooting id={inst.id} due to: Low hashrate per USD!")
                print(f"Hashrate: {hpd}")
                self.vast.reboot_instance(inst.id)

            elif inst.is_running() and hpd <= limit_hashrate:
                #                print_attention(f"Stopping id={inst.id} due to: hashrate is zero")
                print(f"Hashrate: {hpd}")
                #                self.vast.reboot_instance(inst.id)
        #                self.vast.kill_instance(inst.id)

        print_attention("Done!")


    def kill_unable_to_start_instances(self, instances: list[VastInstance]):
        print_attention("Kill instances unable to start...")

        for inst in instances:

            if inst.actual_status == "created":
                print_attention(f"Stopping id={inst.id} due to: Not started!")
                self.vast.kill_instance(inst.id)

        print_attention("Done!")


    def get_vast_instances(self):
        instances = self.vast.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.get_miner_data(instances)
        return instances


    def reset_hours(self, instances):
        print_attention("Reset miners...")
        for instance in instances:
            if instance.miner and instance.miner.duration_hours > 5.0:
                #                if instance.miner.block_cost() > 0.5 or\
                #                    (instance.miner.duration_hours > 10 and instance.miner.block < 1) or \
                #                        (instance.miner.duration_hours > min_hours):

                instance.reset_hours()

        print_attention("Done!")


    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR) and \
               (instance.is_model_a40() or instance.is_model_a5000())


    def set_state(self, new_state: str, info: list = []):
        print_state(new_state, info)


dflop = lambda x: x.flops_per_dphtotal


def sort_on_dflop(instances: list[VastInstance]):
    sorted(instances, key=dflop, reverse=True)


f = Field(ORANGE)
fgray = Field(GRAY)


def print_state(state: str, rows: list = []):
    add_offset = lambda x: " "*5 + x
    offset_rows = list(map(add_offset, rows))

    Menu(state, [""] + offset_rows, 60, col_header=LIGHT_YELLOW, col_row=LIGHT_YELLOW, col_bg=BG_ORANGE).center().print()
    print()


def print_state2(state: str):
    line = "---------------------------"
    print(f.format(line))
    print(f.format(state.center(len(line))))
    print(f.format(line))


def print_attention(info: str):
    print(f.format(info))
