
import time

from datetime import datetime, timedelta
import XenBlocksCache as Cache
from Automation import Automation
from VastInstance import *
from VastClient import VastClient
from VastCache import VastCache
from VastOffer import VastOffer
import config
from Field import *
from statemachine.StateMachine import State, StateMachine
from VastMinerRealtimeTable import VastMinerRealtimeTable
from MinerHistoryTable import MinerHistoryTable, get_balances, calc_effect
from XenBlocksWallet import XenBlocksWallet
from MinerGroup import MinerGroup

import logger as log


START_MINING_M = 48
CHECKPOINT1 = 54
START_PASSIVE_MINING_M = 57   # Do not increase bid prices after this time
CHECKPOINT2 = 1
END_MINING_M = 6


S_START = "Auto Miner"
S_CREATE_MINERS = "Buy GPUs"
S_MANAGE_MINERS = "Miner Startup"
S_KEEP_MINING = "Just Mining"
S_INCREASE_BID = "Increase bid"

DFLOP_MIN_BID = 487
DFLOP_KEEP = 487
DFLOP_BUY = 487

MAX_ALLOCATED_GPUS = 14
MAX_ACTIVE_GPUS = 20


class AutoMinerSM:

    def __init__(self, vast: VastClient, theme: int = 1):
        self.vast: VastClient = vast
        self.vast_cache: VastCache = VastCache(vast)
        self.automation = Automation(vast)
        self.next_state_change: datetime = datetime.now()
        self.difficulty: int = Cache.get_difficulty()
        self.started_instances = []

        self.s_started = State(S_START,
                               [f"DFLOP min: {DFLOP_MIN_BID}",
                                "GPU models: A5000",
                                f"Max allocated GPUs: {MAX_ALLOCATED_GPUS}",
                                f"Max active GPUs: {MAX_ACTIVE_GPUS}"],
                               self.state_started)

        self.s_buy_miners = State(S_CREATE_MINERS,
                                  [f"DFLOP min: {DFLOP_MIN_BID}"],
                                  self.state_startup_miners)

        self.s_manage_miners = State(S_MANAGE_MINERS,
                                     [f"Wait for miners to start up completely"],
                                     self.state_manage_started_miners)

        self.s_mining = State(S_KEEP_MINING,
                              [f"Just keep mining..."],
                              self.state_just_keep_mining)

        self.s_increase_bid = State(S_INCREASE_BID, ["Buying cheap miners"], self.state_increase_bids)

        self.sm = StateMachine("Auto Miner",
                               [self.s_started, self.s_buy_miners, self.s_manage_miners, self.s_mining],
                               theme)


    def get_state_machine(self):
        return self.sm


    #
    #  Mine at the top of the hour when XUNI's are produced
    #
    def state_started(self, time_tick: datetime) -> State:
        log.info(f"Auto Miner next event: {str(_get_next_state_event(1))[11:19]}")

        return self.get_next_state(time_tick)


    def state_startup_miners(self, time_tick: datetime) -> State:

        self.buy_new_miners(DFLOP_BUY)

        instances = self.get_vast_instances()
        self.kill_outbid_instances(instances)

        return self.get_next_state(time_tick)


    def state_manage_started_miners(self, time_tick: datetime) -> State:

#        instances = self.get_vast_instances()
#        VastMinerRealtimeTable(instances).print()

        return self.get_next_state(time_tick)


    def state_just_keep_mining(self, time_tick: datetime) -> State:
        log.info(f"Mining...")

#        instances = self.get_vast_instances()
#        VastMinerRealtimeTable(instances).print()

        self.handle_problematic_instances()

        return self.get_next_state(time_tick)


    def state_increase_bids(self, time_tick: datetime):
        self.log_attention("Increase bids...")

        instances = self.get_vast_instances()
        if not instances:
            self.log_attention("Increase bids failed!")
        else:
            self.increase_bid(instances)

        VastMinerRealtimeTable(instances).print_table()

        self.log_attention("Done!")
        return self.get_next_state(time_tick)


    def get_next_state(self, time_tick: datetime):
        new_difficulty = Cache.get_difficulty()
        difference = abs(new_difficulty - self.difficulty)

        # Only reboot if difficulty has changed with a small value
        # A large change in difficulty indicates that the state machine just started or some other (network?) problem
        if 1 < difference < 6000:
            self.reboot_instances()

        if new_difficulty > 0:
            self.difficulty = new_difficulty

        self.print_difficulty()

        state: State = self.sm.state
        # Start
        if state == self.s_started:
            return self.s_buy_miners

        # Buy Miners
        elif state == self.s_buy_miners:
            self.next_state_change = _get_next_state_event(2)
            return self.s_manage_miners

        # Manage Miners
        elif state == self.s_manage_miners:
            if time_tick.timestamp() > self.next_state_change.timestamp():
                self.next_state_change = _get_next_state_event(3)
            return self.s_mining

        # Mine XUNI
        elif state == self.s_mining:
            if time_tick.timestamp() > self.next_state_change.timestamp():
                return self.s_increase_bid

        # Increase bid
        elif state == self.s_increase_bid:
            return self.s_started

        # No state change
        return state


    def buy_new_miners(self, dflop_min: int):
        self.log_attention(f"Buy A5000 above DFLOP '{dflop_min}' up to max {MAX_ALLOCATED_GPUS} GPUs")

        # Buy new GPUs up to Max Allocation
        if self.get_total_gpus() < MAX_ALLOCATED_GPUS:

            offers: list[VastOffer] = self.automation.offers_A5000(dflop_min)
#            offers2: list[VastOffer] = self.automation.offers_A4000()
#            offers = offers + offers2

            for offer in offers:
                key = f"offer:{offer.id}"
                DbCache().update(key, str(offer.json))

            self.started_instances = self.buy_miners(dflop_min, offers)
        else:
            self.log_attention(f"Skip buying - enough allocated GPUs: '{self.get_total_gpus()}'")

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
        hash_per_usd_min: int = 26000

        all_instances = self.get_vast_instances()


        self.kill_outbid_instances(all_instances)
        self.handle_low_performing_instances(all_instances, hash_per_usd_min)
#        self.kill_unable_to_start_instances(all_instances)


        self.log_attention("Done!")


    def kill_outbid_instances(self, instances: list[VastInstance]):
        self.log_attention("Kill outbid instances...")

        for inst in instances:
            delete = False

            #  This case shouldn't happen but it still does!!!
            #  My bid is lower than the min bid offered on the market place
            #  but I still don't own the instance. So I will delete my bid
            if inst.is_outbid() and (inst.flops_per_dphtotal < (inst.dflop_for_min_bid() - 2)):
                log.error(f"Suspicious instance, will be deleted: {inst.id}")
                delete = True

            elif not inst.is_running() and (inst.dflop_for_min_bid() < DFLOP_KEEP):
                delete = True

            if delete:
                self.log_attention(f"Stopping id={inst.id} due to: outbid")
                print(f"Inst DFLOP min bid: {inst.dflop_for_min_bid()}")
                self.kill_instance(inst)

        self.log_attention("Done!")


    def kill_instances(self, instances: list[VastInstance]):
        for inst in instances:
            self.kill_instance(inst)


    def kill_instance(self, inst: VastInstance):
        if not inst.is_running():
            self.vast.kill_instance(inst.id)


    def reboot_instances(self):
        self.log_attention("Reboot instances...")

        all_instances = self.get_vast_instances()

        for inst in all_instances:
            self.reboot(inst)

        self.log_attention("Done!")


    def reboot(self, inst: VastInstance):

        if inst.is_running():
            self.log_attention(f"Rebooting id={inst.id}!")
            self.vast.reboot_instance(inst.id)
            inst.last_rebooted = datetime.now().timestamp()


    def reboot_miner_group(self, mg: MinerGroup):
        now = int(datetime.now().timestamp())

        for inst in mg.instances:
            next_reboot = datetime.fromtimestamp(inst.last_rebooted) + timedelta(minutes=45)
            if inst.is_running() and now > next_reboot.timestamp():
                self.reboot(inst)


    def handle_low_performing_instances(self, instances: list[VastInstance], hash_per_usd_min: int):
        self.log_attention("Handle low performing instances...")
        min_hash_per_gpu = 1400

        for inst in instances:
            hpg: int = inst.hashrate_per_gpu()
            hpd: int = inst.hashrate_per_dollar()

            if inst.is_miner_online() and hpd <= 0:
                #                print_attention(f"Stopping id={inst.id} due to: hashrate is zero")
                print(f"Rebooting due to Hashrate is zero ({hpd})")
                self.reboot(inst)

            elif not inst.is_running():
                pass

            # Reboot if hashrate is low (but not zero which means there is no miner stats available)
            elif (hpg > 1) and (hpg < min_hash_per_gpu):
                print(f"Rebooting due to Hashrate per gpu={hpg}")
                self.reboot(inst)

            elif (hpd > 1) and (hpd < hash_per_usd_min):
                print(f"Rebooting due to Hashrate per dollar={hpd}")
                self.reboot(inst)

        miner_group_table = MinerHistoryTable(self.vast_cache)
        miner_group_table.print()

        now = int(datetime.now().timestamp())
        balances = get_balances(now, 1.0, 1.1)

        for mg in miner_group_table.miner_groups:
            if mg.id == config.ADDR:
                wallet_balances = balances.get_for_addr(mg.id)
                delta: XenBlocksWallet = mg.balance.difference(wallet_balances)
                effect: float = calc_effect(mg.active_gpus, delta.block)
                if effect < 30.0:
                    print(f"Rebooting miner group: {mg.id}")
                    self.reboot_miner_group(mg)
                else:
                    self.log_attention("No reboot!")

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
                price = price * 1.01

                if offer.flops_per_dphtotal > dflop_min:
                    print(Field.attention(f"Creating instance: {offer.id}"))
                    created_id = self.vast.create_instance(config.ADDR, offer.id, price)
                    bought_instances.append(created_id)

        return bought_instances


    #
    #   Slowly increase bids
    #
    def increase_bid(self, instances):
        self.log_attention(f"Increase bid to DFLOP '{DFLOP_MIN_BID}' until max '{MAX_ACTIVE_GPUS}' active GPUs")

        # A bit fuzzy logic, but don't increase bids if we have a lot of GPUs running already
        if self.get_active_gpus() < MAX_ACTIVE_GPUS:

            outbid_instances = list(filter(lambda x: self.should_bid(x), instances))
            sort_on_dflop(outbid_instances)

    #        if len(outbid_instances) > 0:
            for inst in outbid_instances:
                self.automation.increase_bid_for_instance(inst, DFLOP_MIN_BID, 1.05)
                self.log_attention(f"Increased bid for: {inst.id}")
        else:
            self.log_attention(f"Skip bidding - enough active GPUs: '{self.get_active_gpus()}'")


    def get_active_gpus(self) -> int:
        instances = self.get_vast_instances()
        count = 0

        for inst in instances:
            if inst.is_running():
                count += inst.num_gpus

        return count


    def get_total_gpus(self) -> int:
        instances = self.get_vast_instances()
        count = 0

        for inst in instances:
            count += inst.num_gpus

        return count


    def should_bid(self, instance: VastInstance):
        excluded = [10700258]
        if instance.id in excluded:
            return False

        return instance.dflop_for_min_bid() > DFLOP_MIN_BID and instance.is_outbid()


    def get_vast_instances2(self) -> VastMinerRealtimeTable:
        instances: list[VastInstance] = self.vast_cache.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.load_miner_data(instances)

        return VastMinerRealtimeTable(instances)


    def get_vast_instances(self) -> list[VastInstance]:
        instances = self.vast_cache.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.load_miner_data(instances)
        return instances

    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR)


    def log_attention(self, info: str):
        text = self.sm.state.name + ": " + info
        print(f.format(text))


    def print_difficulty(self):
        now = datetime.now().strftime('%H:%M:%S')
        print()
        field = Field(GOLD)
        print("  ", field.gray(now), "   Diff: ", field.yellow(str(int(self.difficulty/1000))+"K"))


dflop = lambda x: x.flops_per_dphtotal


def sort_on_dflop(instances: list[VastInstance]):
    sorted(instances, key=dflop, reverse=True)


f = Field(ORANGE)
fgray = Field(GRAY)


def _get_next_state_event(minutes: int):
    return datetime.now() + timedelta(minutes=minutes)


