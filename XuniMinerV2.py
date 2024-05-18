
import time

from datetime import datetime, timedelta
from Automation import Automation
from VastInstance import *
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from statemachine.StateMachine import State, StateMachine
from VastMinerRealtimeTable import VastMinerRealtimeTable

import logger


START_MINING_M = 48
CHECKPOINT1 = 54
START_PASSIVE_MINING_M = 57   # Do not increase bid prices after this time
CHECKPOINT2 = 1
END_MINING_M = 6


S_START = "XUNI Miner - Running"
S_CREATE_MINERS = "XUNI - Setup miners"
S_MANAGE_MINERS = "XUNI - Housekeeping jobs"
S_KEEP_MINING = "XUNI - Mining"
S_WAIT_FOR_NEXT_BLOCK = "XUNI - Wait for next Block"
S_TEARDOWN = "XUNI - Stop miners"

DFLOP_MIN = 230
DFLOP_KEEP = 300


class XuniMinerV2:

    def __init__(self, vast, theme: int = 1):
        self.vast: VastClient = vast
        self.automation = Automation(vast)
        self.xuni_miners: list[int] = []
        self.total_blocks = 0
        self.previous_time_tick: datetime = datetime.now()
        self.mining_start: datetime = None
        self.checkpoint1: datetime = None
        self.passive_mining_start = None
        self.checkpoint2: datetime = None
        self.mining_end: datetime = None
        self.reset()

        self.s_started = State(S_START,
                               [f"DFLOP min: {DFLOP_MIN}",
                                "GPU models: A40, A5000",
                                "",
                                f"Mining Start: {START_MINING_M}",
                                f"Mining End:   {END_MINING_M}"],
                               self.state_started)

        self.s_buy_miners = State(S_CREATE_MINERS,
                                  [f"DFLOP min: {DFLOP_MIN}"],
                                  self.state_startup_miners)

        self.s_manage_miners = State(S_MANAGE_MINERS,
                                     ["Passive mining at: " + str(self.passive_mining_start)[11:19]],
                                     self.state_manage_started_miners)

        self.s_mining_xuni = State(S_KEEP_MINING,
                                   ["Mining ends at:   " + str(self.mining_end)[11:19]],
                                   self.state_just_keep_mining)

        self.s_wait_for_next_block = State(S_WAIT_FOR_NEXT_BLOCK, [], self.state_wait_for_next_block)

        self.s_teardown = State(S_TEARDOWN, [], self.state_teardown)

        self.sm = StateMachine("XUNI Miner", [self.s_started, self.s_buy_miners, self.s_manage_miners,
                                self.s_mining_xuni, self.s_wait_for_next_block, self.s_teardown],
                               theme)


    def get_state_machine(self):
        return self.sm


    def reset(self):
        self.total_blocks = 0

        now = datetime.now()

        # Events in current hour
        self.mining_start = now.replace(minute=START_MINING_M)
        self.checkpoint1 = now.replace(minute=CHECKPOINT1)
        self.passive_mining_start = now.replace(minute=START_PASSIVE_MINING_M)

        # Events in next hour
        self.checkpoint2 = now.replace(minute=CHECKPOINT1) + timedelta(hours=1)
#        self.checkpoint2 += timedelta(hours=1)
        self.mining_end = now.replace(minute=END_MINING_M) + timedelta(hours=1)
#        self.mining_end += timedelta(hours=1)


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
    def state_started(self, time_tick: datetime) -> State:

        log.info("Xuni Miner next event: " + str(self.mining_start)[11:19])

        return self.get_next_state(time_tick)

#        now = time_tick
#        if now.timestamp() > self.mining_start.timestamp():
#            return self.s_buy_miners
#        else:
#            log.info("Xuni Miner next event: " + self.s_save_to_history.info[3])

#        return self.s_save_to_history


    def state_startup_miners(self, time_tick: datetime) -> State:

        self.buy_miners_for_xuni(DFLOP_MIN)
        time.sleep(30+60)
        self.reboot_instances(15000)

        return self.s_manage_miners


    def state_manage_started_miners(self, time_tick: datetime) -> State:

        instances = self.get_vast_instances()
        self.reset_hours(instances)

        now = time_tick
        if now.timestamp() < self.passive_mining_start.timestamp():
            pass
#                self.increase_bid(instances)

        self.handle_startup()

        logger.info(f"Mining ends at: {str(self.mining_end)[11:19]}")

        if now.timestamp() > self.passive_mining_start.timestamp():
            return self.s_mining_xuni
        else:
            return self.s_manage_miners


    def state_just_keep_mining(self, time_tick: datetime) -> State:

#            total_blocks = self.get_total_blocks()
#            if total_blocks > 2:
#                return self.s_wait_for_next_block
#            else:
#                return self.s_teardown

        logger.info(f"Mining ends at: {str(self.mining_end)[11:19]}")
        self.handle_problematic_instances()

        if time_tick.timestamp() > self.mining_end.timestamp():

            return self.s_teardown
#            self.total_blocks = self.get_total_blocks()
#            return self.s_wait_for_next_block

        # Mining ends...
        return self.s_mining_xuni


    def state_wait_for_next_block(self, time_tick: datetime) -> State:

        logger.info(f"Total Blocks: {self.total_blocks}")

        total = self.get_total_blocks()

        xuni_miners = self.get_xuni_miners()

        if self.total_blocks == 0:
            self.total_blocks = total
            return self.s_wait_for_next_block

        elif total > self.total_blocks:
            return self.s_teardown

        else:
            return self.s_wait_for_next_block


    def get_next_state(self, time_tick: datetime):
        state: State = self.sm.state

        # Start
        if state == self.s_started:
            if time_tick.timestamp() > self.mining_start.timestamp():
                return self.s_buy_miners

        # Buy Miners
        elif state == self.s_buy_miners:
            return self.s_manage_miners

        # Manage Miners
        elif state == self.s_manage_miners:
            if time_tick.timestamp() > self.passive_mining_start.timestamp():
                return self.s_mining_xuni

        # Mine XUNI
        elif state == self.s_mining_xuni:
            if time_tick.timestamp() > self.mining_end.timestamp():

                self.total_blocks = self.get_total_blocks()
                return self.s_wait_for_next_block

        # Wait for one more block
        elif state == self.s_wait_for_next_block:

            total = self.get_total_blocks()
            if total > self.total_blocks:
                return self.s_teardown

        # Teardown
        elif state == self.s_teardown:
            self.reset()
            return self.s_started

        # No state change
        return state


    def state_teardown(self, time_tick: datetime) -> State:

        instances = self.get_xuni_miners()

        VastMinerRealtimeTable(instances).print_table()

        if len(instances) > 0:
            self.kill_instances(instances)

        self.log_attention("Done!")
        self.reset()

        return self.get_next_state(time_tick)


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


    def reboot_instances(self, hash_per_usd_min: int):
        self.log_attention("Reboot instances...")

        all_instances = self.vast.get_instances()
        self.vast.load_miner_data(all_instances)

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

            if inst.actual_status == "created" or inst.actual_status == "loading":
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
            self.automation.increase_bid_for_instance(top_dflop, 500, 1.02)
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
            logger.error("No XUNI miners found!")

        self.vast.load_miner_data(instances)
        return instances


    def get_vast_instances(self) -> list[VastInstance]:
        instances = self.vast.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.load_miner_data(instances)
        return instances


    def get_total_blocks(self):
        xuni_miners = self.get_xuni_miners()
        total = 0
        for inst in xuni_miners:
            if inst.miner:
                total += inst.miner.block

        return total


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
        text = self.sm.state.name + ": " + info
        print(f.format(text))


dflop = lambda x: x.flops_per_dphtotal


def sort_on_dflop(instances: list[VastInstance]):
    sorted(instances, key=dflop, reverse=True)


f = Field(ORANGE)
fgray = Field(GRAY)


