
import time

from datetime import datetime, timedelta
import XenBlocksCache as Cache
from Automation import Automation
from VastInstance import *
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from statemachine.StateMachine import State, StateMachine
from VastMinerRealtimeTable import VastMinerRealtimeTable
from MinerHistoryTable import MinerHistoryTable

import logger


START_MINING_M = 48
CHECKPOINT1 = 54
START_PASSIVE_MINING_M = 57   # Do not increase bid prices after this time
CHECKPOINT2 = 1
END_MINING_M = 6


S_START = "Running"
S_CREATE_MINERS = "Buy GPUs"
S_MANAGE_MINERS = "Housekeeping jobs"
S_KEEP_MINING = "Just Mining"
S_INCREASE_BID = "Increase bid"

DFLOP_MIN = 480
DFLOP_KEEP = 370

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]


class AutoMiner:

    def __init__(self, vast, theme: int = 1):
        self.vast: VastClient = vast
        self.automation = Automation(vast)
        self.history_table = MinerHistoryTable(self.vast)
        self.next_trigger = None

        self.s_started = State(S_START,
                               [f"DFLOP min: {DFLOP_MIN}",
                                "GPU models: A5000"],
                               self.state_started)

        self.s_buy_miners = State(S_CREATE_MINERS,
                                  [f"DFLOP min: {DFLOP_MIN}"],
                                  self.state_startup_miners)

        self.s_manage_miners = State(S_MANAGE_MINERS,
                                     [f"Manage started miners"],
                                     self.state_manage_started_miners)

        self.s_mining = State(S_KEEP_MINING,
                              [f"Just keep mining..."],
                              self.state_just_keep_mining)

        self.s_increase_bid = State(S_INCREASE_BID, ["Buying cheap miners"], self.state_increase_bids)

#        self.s_teardown = State(S_TEARDOWN, [], self.state_teardown)

        self.sm = StateMachine("Auto Miner",
                               [self.s_started, self.s_buy_miners, self.s_manage_miners, self.s_mining],
                               theme)


    def get_state_machine(self):
        return self.sm


    #
    #  Mine at the top of the hour when XUNI's are produced
    #
    def state_started(self, time_tick: datetime) -> State:

        log.info(f"Auto Miner next event: {str(_get_next_trigger(1))[11:19]}")

        timestamp = int(time_tick.timestamp())

        result = False
        for addr in addr_list:
            snapshot = Cache.get_wallet_balance(addr, timestamp)
            if snapshot:
                log.info("Saving snapshot: " + snapshot.addr)

                result = self.history_table.save_historic_data(snapshot)
                log.info("Done!")

        return self.get_next_state(time_tick)



    def state_startup_miners(self, time_tick: datetime) -> State:

        self.buy_new_miners(DFLOP_MIN)

        return self.get_next_state(time_tick)


    def state_manage_started_miners(self, time_tick: datetime) -> State:

        instances = self.get_vast_instances()
        VastMinerRealtimeTable(instances).print_table()

        self.handle_startup()

        return self.get_next_state(time_tick)


    def state_just_keep_mining(self, time_tick: datetime) -> State:

        logger.info(f"Mining...")
        self.handle_problematic_instances()

        return self.get_next_state(time_tick)


    def state_increase_bids(self, time_tick: datetime):
        self.log_attention("Increase bids...")

        instances = self.get_vast_instances()
        VastMinerRealtimeTable(instances).print_table()

        self.increase_bid(instances)

        self.log_attention("Done!")
        return self.get_next_state(time_tick)


    def get_next_state(self, time_tick: datetime):
        state: State = self.sm.state

        # Start
        if state == self.s_started:
            self.next_trigger = _get_next_trigger(2)
            return self.s_buy_miners

        # Buy Miners
        elif state == self.s_buy_miners:
            if time_tick.timestamp() > self.next_trigger.timestamp():
                return self.s_manage_miners

        # Manage Miners
        elif state == self.s_manage_miners:
            self.next_trigger = _get_next_trigger(3)
            return self.s_mining

        # Mine XUNI
        elif state == self.s_mining:
            if time_tick.timestamp() > self.next_trigger.timestamp():
                self.total_blocks = self.get_total_blocks()
                return self.s_increase_bid

        # Increase bid
        elif state == self.s_increase_bid:

            return self.s_started

        # No state change
        return state


    def buy_new_miners(self, dflop_min: int):
        self.log_attention("Buy miners for XUNI...")

#        offers1: list[VastOffer] = self.automation.offers_A40(dflop_min)
        offers: list[VastOffer] = self.automation.offers_A5000(dflop_min)

        self.buy_miners(dflop_min, offers)

        self.log_attention("Done!")


    def handle_startup(self):
        self.log_attention("Handle Startup...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 15000
        all_instances = self.get_vast_instances()

#        self.kill_outbid_instances(all_instances)
        self.handle_low_performing_instances(all_instances, hash_per_usd_min)
#        self.kill_unable_to_start_instances(all_instances)


    def handle_problematic_instances(self):
        self.log_attention("Handle problem instances...")

        # Minimum hashrate per dollar, purge instances below
        hash_per_usd_min: int = 15000

        all_instances = self.get_vast_instances()

#        self.kill_outbid_instances(all_instances)
        self.handle_low_performing_instances(all_instances, hash_per_usd_min)
#        self.kill_unable_to_start_instances(all_instances)

        self.log_attention("Done!")


    def kill_outbid_instances(self, instances: list[VastInstance]):
        self.log_attention("Kill outbid instances...")

        for inst in instances:
            if inst.is_outbid() and (inst.flops_per_dphtotal < 400):
                self.log_attention(f"Stopping id={inst.id} due to: outbid")
                print(f"Inst DFLOP: {inst.flops_per_dphtotal}")
                self.kill_instance(inst)

        self.log_attention("Done!")



    def kill_instances(self, instances: list[VastInstance]):
        for inst in instances:
            self.kill_instance(inst)


    def kill_instance(self, inst: VastInstance):
        if inst.flops_per_dphtotal < 400:
            self.vast.kill_instance(inst.id)


    def reboot_instances(self, hash_per_usd_min: int):
        self.log_attention("Reboot instances...")

        all_instances = self.get_vast_instances()

        for inst in all_instances:
            self.reboot(inst, hash_per_usd_min)

        self.log_attention("Done!")


    def reboot(self, inst: VastInstance, hash_per_usd_min: int):
        hpd = inst.hashrate_per_dollar()

        # Reboot if hashrate is low but not zero
        if inst.is_running() and inst.is_miner_online() and (hpd < hash_per_usd_min) and (hpd > 1):

            self.log_attention(f"Rebooting id={inst.id} due to: Low hashrate per USD!")
            print(f"Hashrate: {hpd}")
            self.vast.reboot_instance(inst.id)


    def handle_low_performing_instances(self, instances: list[VastInstance], hash_per_usd_min: int):
        self.log_attention("Handle low performing instances...")

        for inst in instances:
            hpd: int = inst.hashrate_per_dollar()

            # Reboot if hashrate is low but not zero
            if inst.is_running() and (hpd > 1) and (hpd < hash_per_usd_min):
                self.reboot(inst, hash_per_usd_min)

            elif inst.is_running() and hpd <= 0:
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

#        if len(outbid_instances) > 0:
        for inst in outbid_instances:
            self.automation.increase_bid_for_instance(inst, DFLOP_MIN, 1.02)
            self.log_attention(f"Increased bid for: {inst.id}")


    def should_bid(self, instance: VastInstance):
        excluded = [10700258]
        if instance.id in excluded:
            return False

        return instance.flops_per_dphtotal > DFLOP_MIN and instance.is_outbid()


    def get_vast_instances(self) -> list[VastInstance]:
        instances = self.vast.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.get_miner_data(instances)
        return instances


    def get_total_blocks(self):
        xuni_miners = self.get_vast_instances()
        total = 0
        for inst in xuni_miners:
            if inst.miner:
                total += inst.miner.block

        return total


    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR)


    def log_attention(self, info: str):
        text = self.sm.state.name + ": " + info
        print(f.format(text))


dflop = lambda x: x.flops_per_dphtotal


def sort_on_dflop(instances: list[VastInstance]):
    sorted(instances, key=dflop, reverse=True)


f = Field(ORANGE)
fgray = Field(GRAY)


def _get_next_trigger(minutes: int):
    return datetime.now() + timedelta(minutes=minutes)

