
import time

from Automation import Automation
from VastInstance import *
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from Menu import Menu
from VastMinerTable import VastMinerTable

START_MINING_M = 48
CHECKPOINT1 = 54
START_PASSIVE_MINING_M = 57   # Do not increase bid prices after this time
CHECKPOINT2 = 1
END_MINING_M = 6


S_START_MINING = "XUNI Miner running..."
S_CREATE_MINERS = "Setup miners for XUNI..."
S_MANAGE_MINERS = "Increase bids housekeeping jobs etc..."
S_KEEP_MINING = "Just keep mining..."



class XuniMiner:

    def __init__(self, vast):
        self.vast: VastClient = vast
        self.automation = Automation(vast)
        self.hours = 0
        self.minutes: int = 0
        self.state: str = "None"
        self.mining_start = None
        self.checkpoint1: datetime = None
        self.passive_mining_start = None
        self.checkpoint2: datetime = None
        self.mining_end = None
        self.reset()


    def reset(self):
        now = datetime.now()
        next_hour = (now.hour + 1) if now.hour < 23 else 0
        self.mining_start = now.replace(minute=START_MINING_M)
        self.checkpoint1 = now.replace(minute=CHECKPOINT1)
        self.passive_mining_start = now.replace(minute=START_PASSIVE_MINING_M)
        self.checkpoint2 = now.replace(hour=next_hour, minute=CHECKPOINT1)
        self.mining_end = now.replace(hour=next_hour, minute=END_MINING_M)


    def mine_xuni(self):
        dflop_min = 199

        self.set_state(S_START_MINING, [f"DFLOP min: {dflop_min}", f"GPU models: A40, A5000"])
        print_info("Mining Start: " + str(self.mining_start)[11:19])
        print_info("Mining End: " + str(self.mining_end)[11:19])

        while True:
            now = get_current_time()

            #
            #  Mine at the top of the hour when XUNI's are produced
            #
            if now.timestamp() > self.mining_start.timestamp():
                self.state_startup_miners(dflop_min)

                # Begin next iteration
                self.reset()
                self.set_state(S_START_MINING, [f"DFLOP min: {dflop_min}", f"GPU models: A40, A5000"])
                print_info("Mining Start: " + str(self.mining_start)[11:19])
                print_info("Mining End: " + str(self.mining_end)[11:19])

            time.sleep(60)


    def state_startup_miners(self, dflop_min):
        self.set_state(S_CREATE_MINERS)

#        now = get_current_time()

#        if now.timestamp() > self.checkpoint1.timestamp():
        self.buy_miners(dflop_min)

        # Do housekeeping of newly started miners...
        print_state("Wait 3 minutes and check for problem instances...")
        time.sleep(3*60)
        self.state_manage_started_miners()

        # Do the mining
        self.state_just_keep_mining()


    def state_manage_started_miners(self):
        self.set_state(S_MANAGE_MINERS)

        while True:
            now = get_current_time()
            #            print("Min1: ", now.minute)
            #            print("Min2: ", self.checkpoint1.minute)

            instances = self.get_vast_instances()

            if now.timestamp() < self.passive_mining_start.timestamp():
                pass
#                self.increase_bid(instances)
            else:
                break

            self.handle_startup(instances)

            print_info(f"Mining ends at: {str(self.mining_end)[11:19]}")
            time.sleep(60)


    def state_just_keep_mining(self):
        # Mine until XUNI is stopped being produced
        self.set_state(S_KEEP_MINING)

        while True:
            now = get_current_time()
            #            print("Min1: ", now.minute)
            #            print("Min2: ", self.checkpoint1.minute)

            # Mining ends...
            if now.timestamp() > self.mining_end.timestamp():
                self.state_kill_all_running_instances()
                break

            print_info(f"Mining ends at: {str(self.mining_end)[11:19]}")
            time.sleep(1*60)
            instances = self.get_vast_instances()
            self.handle_problematic_instances(instances)
            time.sleep(1*60)


    def state_kill_all_running_instances(self):
        dflop_limit = 290
        self.set_state("Kill running instances...")
        instances = self.get_vast_instances()

        VastMinerTable(instances).print_table()

        for inst in instances:
            # Spare the ones with high DFLOP value
            if inst.flops_per_dphtotal < dflop_limit:
                self.vast.kill_instance(inst.id)


    def buy_miners(self, dflop_min: int):
        offers1: list[VastOffer] = self.automation.offers_A40(dflop_min)
        offers2: list[VastOffer] = self.automation.offers_A5000(220)
        offers = offers1 + offers2

        if len(offers) == 0:
            print(Field.attention(f"No offers below required flops per dph found: {dflop_min}"))
        else:
            for offer in offers:
                #                        best_offer: VastOffer = offers
                # Increase bid price
                price: float = offer.min_bid
                price = price * 1.02

                if offer.flops_per_dphtotal > dflop_min:
                    print(Field.attention(f"Creating instance: {offer.id}"))
                    self.vast.create_instance(config.ADDR, offer.id, price)
                else:
                    print(Field.attention(f"No offers below required flops per dph found: {dflop_min}"))
                    print(Field.attention(f"Best offer was: {offer.flops_per_dphtotal}"))


    def handle_startup(self, instances: list[VastInstance]):
        print_attention("Handle problem instances...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 18000
        dflop_min: int = 300

#        self.kill_outbid_instances(instances, dflop_min)
        self.handle_low_performing_instances(instances, hash_per_usd_min)
        self.kill_unable_to_start_instances(instances)


    def handle_problematic_instances(self, instances: list[VastInstance]):
        print_attention("Handle problem instances...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 18000
        dflop_min: int = 300

        self.kill_outbid_instances(instances, dflop_min)
        self.handle_low_performing_instances(instances, hash_per_usd_min)
        self.kill_unable_to_start_instances(instances)


    def kill_outbid_instances(self, instances: list[VastInstance], dflop_limit: int):
        print_attention("Kill outbid instances...")

        for inst in instances:
            if inst.is_outbid() and (inst.flops_per_dphtotal < dflop_limit):
                print_attention(f"Stopping id={inst.id} due to: outbid")
                print(f"Inst DFLOP: {inst.flops_per_dphtotal}")
                self.vast.kill_instance(inst.id)


    def handle_low_performing_instances(self, instances: list[VastInstance], hash_per_usd_min: int):
        print_attention("Handle low performing instances...")

        limit_hashrate = 10.0

        for inst in instances:
            hpd = inst.hashrate_per_dollar()

            # Reboot if hashrate is low but not zero
            if (hpd > limit_hashrate) and (hpd < hash_per_usd_min):
                print_attention(f"Rebooting id={inst.id} due to: Low hashrate per USD!")
                print(f"Hashrate: {hpd}")
                self.vast.reboot_instance(inst.id)

            elif hpd <= limit_hashrate:
                #                print_attention(f"Stopping id={inst.id} due to: hashrate is zero")
                print(f"Hashrate: {hpd}")
                #                self.vast.reboot_instance(inst.id)
    #                self.vast.kill_instance(inst.id)


    def kill_unable_to_start_instances(self, instances: list[VastInstance]):
        print_attention("Kill unable to start instances...")

        for inst in instances:

            if inst.actual_status == "created":
                print_attention(f"Stopping id={inst.id} due to: Not started!")
                self.vast.kill_instance(inst.id)


    #
    #   Slowly increase bids
    #
    def increase_bid(self, instances: list[VastInstance]):
        self.set_state("Increase Bid Price...")

        outbid_instances = list(filter(lambda x: self.should_bid(x), instances))
        sort_on_dflop(outbid_instances)

        if len(outbid_instances) > 0:
            top_dflop = outbid_instances[0]
            self.automation.increase_bid_for_instance(top_dflop, 1.02)
            print_attention(f"Increased bid for: {top_dflop.id}")

#        self.automation.increase_bid(outbid_instances, 1.02)


    def should_bid(self, instance: VastInstance):
        excluded = [10700258]
        if instance.id in excluded:
            return False

        return instance.is_outbid() and instance.num_gpus > 0


    def get_vast_instances(self):
        instances = self.vast.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.get_miner_data(instances)
        return instances


    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR) and \
               (instance.is_model_a40() or instance.is_model_a5000())


    def set_state(self, new_state: str, info: list = []):
        print_state(new_state, info)


dflop = lambda x: x.flops_per_dphtotal


def sort_on_dflop(instances: list[VastInstance]):
    sorted(instances, key=dflop, reverse=True)


def get_current_time() -> datetime:
    now = datetime.now()
    print_info(str(now)[11:19])
    return now


f = Field(ORANGE)
fgray = Field(GRAY)


def print_state(state: str, rows: list = []):
    add_offset = lambda x: " "*5 + x
    offset_rows = list(map(add_offset, rows))

    Menu(state, [""] + offset_rows, 60, ORANGE).center().print()
    print()


def print_state2(state: str):
    line = "---------------------------"
    print(f.format(line))
    print(f.format(state.center(len(line))))
    print(f.format(line))


def print_info(info: str):
    print(fgray.format(info))


def print_attention(info: str):
    print(f.format(info))
