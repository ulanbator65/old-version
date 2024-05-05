
import time

from Automation import Automation
from VastInstance import *
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from statemachine.StateMachine import State, StateMachine
from VastMinerTable import VastMinerTable

import logger


START_MINING_M = 46
CHECKPOINT1 = 54
START_PASSIVE_MINING_M = 57   # Do not increase bid prices after this time
CHECKPOINT2 = 1
END_MINING_M = 6


S_START_MINING = "XUNI Miner running"
S_CREATE_MINERS = "Setup XUNI miners"
S_MANAGE_MINERS = "Housekeeping jobs"
S_KEEP_MINING = "Mining XUNI"
S_TEARDOWN = "Stop XUNI miners"

DFLOP_KEEP = 300


class XuniMinerV2:

    def __init__(self, vast):
        self.vast: VastClient = vast
        self.automation = Automation(vast)
        self.xuni_miners: list[int] = []
        self.hours = 0
        self.minutes: int = 0
        self.state: str = "None"
        self.mining_start = None
        self.checkpoint1: datetime = None
        self.passive_mining_start = None
        self.checkpoint2: datetime = None
        self.mining_end = None
        self.reset()
        self.dflop_min = 215

        self.s_started = State(S_START_MINING,
                               [f"DFLOP min: {self.dflop_min}",
                         f"GPU models: A40, A5000",
                         "",
                         "Mining Start: " + str(self.mining_start)[11:19],
                         "Mining End:   " + str(self.mining_end)[11:19]],
                               self.mine_xuni)

        self.s_buy_miners = State(S_CREATE_MINERS,
                                  [f"DFLOP min: {self.dflop_min}"],
                                  self.state_startup_miners)

        self.s_manage_miners = State(S_MANAGE_MINERS,
                                     ["Passive mining at: " + str(self.passive_mining_start)[11:19]],
                                     self.state_manage_started_miners)

        self.s_mining_xuni = State(S_KEEP_MINING,
                                   ["Mining ends at:   " + str(self.mining_end)[11:19]],
                                   self.state_just_keep_mining)

        self.s_teardown = State(S_TEARDOWN, [], self.state_kill_all_xuni_miners)

        self.sm = StateMachine([self.s_started, self.s_buy_miners, self.s_manage_miners, self.s_mining_xuni, self.s_teardown])


    def get_state_machine(self):
        return self.sm


    def reset(self):
        now = datetime.now()
#        now + timedelta(days=5, hours=1)

#        next_hour = (now.hour + 1) if now.min < 10 else now.hour
        next_hour = (now.hour + 1) if now.hour < 23 else 0
        self.mining_start = now.replace(minute=START_MINING_M)
        self.checkpoint1 = now.replace(minute=CHECKPOINT1)
        self.passive_mining_start = now.replace(minute=START_PASSIVE_MINING_M)

        if next_hour > 0:
            self.checkpoint2 = now.replace(hour=next_hour, minute=CHECKPOINT1)
            self.mining_end = now.replace(hour=next_hour, minute=END_MINING_M)
        else:
            next_day = (now.day + 1)
            self.checkpoint2 = now.replace(day=next_day, hour=0, minute=CHECKPOINT1)
            self.mining_end = now.replace(day=next_day, hour=0, minute=END_MINING_M)



    def mine_xuni_test(self) -> State:
        dflop_min = 240

        self.xuni_miners = [10754563, 10754564, 10754566]

        self.buy_miners_for_xuni(dflop_min)
        time.sleep(30)
        xuni_miners = self.get_xuni_miners()
        self.kill_unable_to_start_instances(xuni_miners)

        return self.s_started


    #
    #  Mine at the top of the hour when XUNI's are produced
    #
    def mine_xuni(self, time_tick: datetime) -> State:

        now = time_tick
        if now.timestamp() > self.mining_start.timestamp():
            return self.s_buy_miners
        else:
            log.print_warning("XuniMiner next event: " + self.s_started.info[3])

        return self.s_started


    def state_startup_miners(self, time_tick: datetime) -> State:

        self.buy_miners_for_xuni(self.dflop_min)
        time.sleep(30+60)

        return self.s_manage_miners


    def state_manage_started_miners(self, time_tick: datetime) -> State:

        instances = self.get_vast_instances()
        self.reset_hours(instances)

        now = time_tick
#        print("Min1: ", now.minute)
#        print("Min2: ", self.checkpoint1.minute)

        if now.timestamp() < self.passive_mining_start.timestamp():
            pass
#                self.increase_bid(instances)

        self.handle_startup()

        logger.print_info(f"Mining ends at: {str(self.mining_end)[11:19]}")

        if now.timestamp() > self.passive_mining_start.timestamp():
            return self.s_mining_xuni
        else:
            return self.s_manage_miners


    def state_just_keep_mining(self, time_tick: datetime) -> State:

        # Mining ends...
        if time_tick.timestamp() > self.mining_end.timestamp():
            return self.s_teardown

        logger.print_info(f"Mining ends at: {str(self.mining_end)[11:19]}")
        self.handle_problematic_instances()

        return self.s_mining_xuni


    def state_kill_all_xuni_miners(self, time_tick: datetime) -> State:

        instances = self.get_xuni_miners()

        VastMinerTable(instances).print_table()

        if len(instances) > 0:
            self.kill_instances(instances)

        self.log_attention("Done!")
        self.reset()
        return self.s_started


    def buy_miners_for_xuni(self, dflop_min: int):
        self.log_attention("Buy miners for XUNI...")

        offers1: list[VastOffer] = self.automation.offers_A40(dflop_min)
        offers2: list[VastOffer] = self.automation.offers_A5000(dflop_min)

        self.xuni_miners = self.buy_miners(dflop_min, offers1 + offers2)

        self.log_attention("Done!")


    def handle_startup(self):
        self.log_attention("Handle Startup...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 15000
        all_instances = self.get_vast_instances()
        xuni_miners = self.get_xuni_miners()

        self.kill_outbid_instances(xuni_miners)
        self.handle_low_performing_instances(all_instances, hash_per_usd_min)
        self.kill_unable_to_start_instances(xuni_miners)


    def handle_problematic_instances(self):
        self.log_attention("Handle problem instances...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 15000

        xuni_miners = self.get_xuni_miners()
        all_instances = self.get_vast_instances()

        self.kill_outbid_instances(xuni_miners)
        self.handle_low_performing_instances(all_instances, hash_per_usd_min)
        self.kill_unable_to_start_instances(xuni_miners)

        self.log_attention("Done!")


    def kill_outbid_instances(self, instances: list[VastInstance]):
        self.log_attention("Kill outbid instances...")

        for inst in instances:
            if inst.is_outbid() and (inst.flops_per_dphtotal < DFLOP_KEEP):
                self.log_attention(f"Stopping id={inst.id} due to: outbid")
                print(f"Inst DFLOP: {inst.flops_per_dphtotal}")
                self.kill_instance(inst)

        self.log_attention("Done!")



    def kill_instances(self, instances: list[VastInstance]):
        for inst in instances:
            self.vast.kill_instance(inst.id)


    def kill_instance(self, inst: VastInstance):
        if inst.flops_per_dphtotal < 350:
            self.vast.kill_instance(inst.id)


    def reboot_instances(self, instances: list[VastInstance], hash_per_usd_min: int):
        self.log_attention("Reboot instances...")

        all_instances = self.vast.get_instances()
        self.vast.get_miner_data(all_instances)


    #        for inst in instances:
        for inst in all_instances:
            hpd = inst.hashrate_per_dollar()

            # Reboot if hashrate is low but not zero
            if inst.is_running() and (hpd < hash_per_usd_min):
                self.log_attention(f"Rebooting id={inst.id} due to: Low hashrate per USD!")
                print(f"Hashrate: {hpd}")
                self.vast.reboot_instance(inst.id)

        self.log_attention("Done!")


    def handle_low_performing_instances(self, instances: list[VastInstance], hash_per_usd_min: int):
        self.log_attention("Handle low performing instances...")

        limit_hashrate = 0

        for inst in instances:
            hpd: int = inst.hashrate_per_dollar()

            # Reboot if hashrate is low but not zero
            if inst.is_running() and (hpd >= limit_hashrate) and (hpd < hash_per_usd_min):
                self.log_attention(f"Rebooting id={inst.id} due to: Low hashrate per USD!")
                print(f"Hashrate: {hpd}")
                self.vast.reboot_instance(inst.id)

            elif inst.is_running() and hpd <= limit_hashrate:
                #                print_attention(f"Stopping id={inst.id} due to: hashrate is zero")
                print(f"Hashrate: {hpd}")
                #                self.vast.reboot_instance(inst.id)
    #                self.kill_instance(inst)

        self.log_attention("Done!")


    def kill_unable_to_start_instances(self, instances: list[VastInstance]):
        self.log_attention("Kill instances unable to start...")

        to_kill = []

        for inst in instances:

            if inst.actual_status == "created" and (inst.flops_per_dphtotal < DFLOP_KEEP):
                self.log_attention(f"Stopping id={inst.id} due to: Not started!")
                to_kill.append(inst)
#                self.kill_instance(inst)

        self.kill_instances(to_kill)
#        self.vast.kill_instances(self.xuni_miners)
        self.log_attention("Done!")


    def buy_miners(self, dflop_min: int, offers: list[VastOffer]) -> list[int]:
        bought_instances = []

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
                    created_id = self.vast.create_instance(config.ADDR, offer.id, price)
                    bought_instances.append(created_id)

        return bought_instances


    #
    #   Slowly increase bids
    #
    def increase_bid(self, instances: list[VastInstance]):

        outbid_instances = list(filter(lambda x: self.should_bid(x), instances))
        sort_on_dflop(outbid_instances)

        if len(outbid_instances) > 0:
            top_dflop = outbid_instances[0]
            self.automation.increase_bid_for_instance(top_dflop, 1.02)
            self.log_attention(f"Increased bid for: {top_dflop.id}")

#        self.automation.increase_bid(outbid_instances, 1.02)


    def should_bid(self, instance: VastInstance):
        excluded = [10700258]
        if instance.id in excluded:
            return False

        return instance.is_outbid() and instance.num_gpus > 0


    def get_xuni_miners(self) -> list[VastInstance]:
        instances = self.vast.get_selected_instances(self.xuni_miners)

        if len(instances) < 1:
            logger.print_error("No XUNI miners found!")

        self.vast.get_miner_data(instances)
        return instances


    def get_vast_instances(self) -> list[VastInstance]:
        instances = self.vast.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.get_miner_data(instances)
        return instances


    def reset_hours(self, instances):
        self.log_attention("Reset miners...")
        for instance in instances:
            if instance.miner and instance.miner.duration_hours > 5.0:
                #                if instance.miner.block_cost() > 0.5 or\
                #                    (instance.miner.duration_hours > 10 and instance.miner.block < 1) or \
                #                        (instance.miner.duration_hours > min_hours):

                instance.reset_hours()

        self.log_attention("Done!")


    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR) and \
               (instance.is_model_a40() or instance.is_model_a5000())


    def log_attention(self, info: str):
        text = self.sm.next_state.name + ": " + info
        print(f.format(text))


dflop = lambda x: x.flops_per_dphtotal


def sort_on_dflop(instances: list[VastInstance]):
    sorted(instances, key=dflop, reverse=True)


f = Field(ORANGE)
fgray = Field(GRAY)


