
import time

from Automation import Automation
from VastInstance import *
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from Menu import Menu
from VastMinerTable import VastMinerTable

START_MINING_M = 41
START_PASSIVE_MINING_M = 59   # Do not increase bid prices after this time
END_MINING_M = 7


f = Field(ORANGE)
fgray = Field(GRAY)

S_START_MINING = "XUNI Miner running..."
S_CREATE_MINERS = "Setup miners for XUNI..."
S_KEEP_MINING = "Just keep mining..."



class XuniMiner:

    def __init__(self, vast):
        self.vast: VastClient = vast
        self.automation = Automation(vast)
        self.hours = 0
        self.minutes: int = 0
        self.state: str = "None"
        self.mining_start = None
        self.passive_mining_start = None
        self.mining_end = None
        self.reset()


    def reset(self):
        now = datetime.now()
        next_hour = now.hour + 1
        self.mining_start = now.replace(minute=START_MINING_M)
        self.passive_mining_start = now.replace(hour=next_hour, minute=START_PASSIVE_MINING_M)
        self.mining_end = now.replace(hour=next_hour, minute=END_MINING_M)


    def mine_xuni(self):
        dflop_min = 199

        self.set_state(S_START_MINING, [f"DFLOP min: {dflop_min}", f"GPU models: A40, A5000"])
        print_info("Mining Start: " + str(self.mining_start)[11:16])
        print_info("Mining End: " + str(self.mining_end)[11:16])

        while True:
            now = get_current_time()

            #
            #  Mine at the top of the hour when XUNI's are produced
            #
            if now > self.mining_start.timestamp():
                self.state_startup_miners(dflop_min)
                # Begin next iteration
                self.reset()
                self.set_state(S_START_MINING, [f"DFLOP min: {dflop_min}", f"GPU models: A40, A5000"])
                print_info("Mining Start: " + str(self.mining_start)[11:16])
                print_info("Mining End: " + str(self.mining_end)[11:16])

            time.sleep(60)


    def state_startup_miners(self, dflop_min):
        self.set_state(S_CREATE_MINERS)

        self.buy_miners(dflop_min)

        VastMinerTable(self.get_vast_instances()).print_table()

        # Check for not started instances
        print_state("Wait 3 minutes and check for problematic instances...")
        time.sleep(3*60)
        self.state_kill_problematic_instances()

        # Do the mining
        self.state_just_keep_mining()


    def state_kill_problematic_instances(self):
        self.set_state("Purge problem instances...")
        selected = self.get_vast_instances()

        for inst in selected:
#            if (inst.actual_status == "created") or (inst.hashrate() < 900):
            print(f"Inst hashrate: {inst.hashrate()}")
            if inst.actual_status == "created":
                print_info(f"Stopping {inst.id}..")
                self.vast.kill_instance(inst.id)


    def state_just_keep_mining(self):
        # Mine until XUNI is stopped being produced
        self.set_state(S_KEEP_MINING)
        while True:
            now = get_current_time()

            if now < self.passive_mining_start.timestamp():
                self.increase_bid()

#            if minutes > END_MINING_M:
            if now > self.mining_end.timestamp():
                self.state_kill_all_running_instances()
                break

            print_info(f"Mining ends at: {self.mining_end}")
            time.sleep(60)


    def state_kill_all_running_instances(self):
        self.set_state("Kill running instances...")
        selected = self.get_vast_instances()

#        for inst in selected:
#            self.vast.kill_instance(inst.id)


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


    def increase_bid(self):
        self.set_state("Increase Bid Price...")

        instances = self.get_vast_instances()
        outbid_instances = list(filter(lambda x: self.should_bid(x), instances))

        self.automation.increase_bid(outbid_instances, 1.04)


    def should_bid(self, instance: VastInstance):
        return instance.is_outbid() and instance.num_gpus > 2


    def get_vast_instances(self):
        instances = self.vast.get_instances()
        return list(filter(lambda x: self.is_managed_instance(x), instances))


    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR) and \
               (instance.is_model_a40() or instance.is_model_a5000())


    def set_state(self, new_state: str, info: list = []):
        print_state(new_state, info)


def get_current_time() -> float:
    now = datetime.now()
    print_info(str(now)[11:16])
    return now.timestamp()


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
