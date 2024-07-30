import XenBlocksCache as Cache
from db.CacheLock import CacheLock
from Automation import Automation
from VastInstance import *
from VastClient import VastClient
from VastCache import VastCache
from VastOffer import VastOffer
from VastTemplate import VastTemplate
import config
from Field import *
from statemachine.StateMachine import State, StateMachine
from VastMinerRealtimeTable import VastMinerRealtimeTable
from MinerPerformanceTable import MinerPerformanceTable, get_balances, calc_effect
from XenBlocksWallet import XenBlocksWallet
from MinerGroup import MinerGroup

import logger as log


START_MINING_M = 48
CHECKPOINT1 = 54
START_PASSIVE_MINING_M = 57   # Do not increase bid prices after this time
CHECKPOINT2 = 1
END_MINING_M = 6


S_START = "VAST Bot"
S_BUY_GPUS = "Buy GPUs"
S_SELL_GPUS = "Sell GPUs"
S_MANAGE_MINERS = "Manage Miners"
S_PURGE = "Purge underperforming instance"
S_INCREASE_BID = "Increase bid"

DEFAULT = 800
DFLOP_MIN_BID = DEFAULT
DFLOP_KEEP = DEFAULT
DFLOP_BUY = DEFAULT
        
MIN_HASH_PER_GPU = 2100
# Minimum hashrate per dollar, purge instances below
HASH_PER_USD_MIN: int = 72000


MAX_ALLOCATED_GPUS = int(config.MAX_GPU)
MAX_ACTIVE_GPUS = 98

TARGET_BLOCK_COST = 0.033


#
# Buy cheap VAST instances
# Sell instances when they become expensive
#
# Main functionality is buying GPUs cheap and selling them when they become expensive.
# Buying here means allocating by placing the best bid on the price per hour.
# Selling means deallocating (returning) an allocated instance.
#
# Additonally:
# Monitor XenBlocks miner performance
# Purge instances where miners are not performing as expected and it can't be resolved with a reboot
# Reboot instances when they are underperforming
#


class VastTradingBotSM:

    def __init__(self, vast: VastClient, theme: int = 1):
        self.vast: VastClient = vast
        self.template = VastTemplate(config.API_KEY)
        self.vast_cache: VastCache = VastCache(vast)
        self.automation = Automation(vast)
        self.difficulty: int = Cache.get_difficulty()
        self.started_instances = []
        self.count = 0
        self.cache_lock = CacheLock()

        self.s_started = State(1, S_START,
                               [f"DFLOP min: {DFLOP_MIN_BID}",
                                "GPU models: A5000",
                                f"Max allocated GPUs: {MAX_ALLOCATED_GPUS}",
                                f"Max active GPUs: {MAX_ACTIVE_GPUS}"],
                               self.state_started)

        self.s_buy_gpus = State(2, S_BUY_GPUS,
                                [f"DFLOP min: {DFLOP_MIN_BID}"],
                                self.state_buy_gpus)

        self.s_sell_gpus = State(3, S_SELL_GPUS,
                                 [f""],
                                 self.state_sell_gpus)

        self.s_manage_miners = State(4, S_MANAGE_MINERS,
                                     [f"Just keep mining..."],
                                     self.state_manage_miners)

        self.s_purge = State(5, S_PURGE,
                             [f"Purge underperforming instances..."],
                             self.state_purge_miners)

        self.s_increase_bid = State(6, S_INCREASE_BID, ["Buying cheap miners"], self.state_increase_bids)

        self.sm = StateMachine("Auto Miner",
                               [self.s_started, self.s_sell_gpus, self.s_buy_gpus, self.s_manage_miners],
                               theme)


    def get_state_machine(self):
        return self.sm


    #
    #  Mine at the top of the hour when XUNI's are produced
    #
    def state_started(self, time_tick: datetime) -> State:
        log.info(f"Auto Miner next event: {str(_get_next_state_event(1))[11:19]}")

        return self.get_next_state(time_tick)


    # Buy cheap GPUs
    def state_buy_gpus(self, time_tick: datetime) -> State:
        self.cache_lock.aquire_lock(config.ADDR)

        self.buy_new_miners(DFLOP_BUY)

        self.cache_lock.release_lock()
        return self.get_next_state(time_tick)


    # Sell expensive GPUs - i.e. delete outbid instances
    def state_sell_gpus(self, time_tick: datetime) -> State:

        instances = self.get_vast_instances()
        VastMinerRealtimeTable(instances).print_table()

#        self.kill_outbid_instances(instances)

        return self.get_next_state(time_tick)


    def state_manage_miners(self, time_tick: datetime) -> State:
        log.info(f"Manage miners...")

        all_instances = self.get_vast_instances()
        self.handle_low_performing_instances(all_instances, HASH_PER_USD_MIN)

        return self.get_next_state(time_tick)


    def state_purge_miners(self, time_tick: datetime) -> State:
        instances = self.get_vast_instances()
        VastMinerRealtimeTable(instances).print_table()
        self.kill_outbid_instances(instances)
        self.purge_instances()
        return self.get_next_state(time_tick)


    def state_increase_bids(self, time_tick: datetime):
        self.log_attention("Increase bids...")

        instances = self.get_vast_instances()
        VastMinerRealtimeTable(instances).print_table()

        if instances:
            self.increase_bid(instances)

        self.log_attention("Done!")
        return self.get_next_state(time_tick)


    def get_next_state(self, time_tick: datetime):
        new_difficulty = Cache.get_difficulty()
        difference = abs(new_difficulty - self.difficulty)

        # Only reboot if difficulty has changed with a small value
        # A large change in difficulty indicates that the state machine just started or some other (network?) problem
        if 1 < difference < 6000:
            self.log_attention("Reboot instances due to change in difficulty!")
#            self.reboot_instances()

        if new_difficulty > 0:
            self.difficulty = new_difficulty

        self.print_difficulty()

        #
        # Change State
        #
        state: State = self.sm.state
        # Start
        if state == self.s_started:
            return self.s_buy_gpus

        # Buy Miners
        elif state == self.s_buy_gpus:
            return self.s_sell_gpus

        # Kill Outbid Miners
        elif state == self.s_sell_gpus:
            return self.s_manage_miners

        # Manage Miners
#        elif state == self.s_manage_miners:
#            return self.s_manage_miners

        # Mine
        elif state == self.s_manage_miners:
            self.count += 1
            if self.count >= 1:
                self.count = 0
                return self.s_purge

        # Purge bad instancez
        elif state == self.s_purge:
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

            offers: list = self.automation.offers_A5000(dflop_min)
#            offers2: list = self.automation.offers_A4000()
#            offers = offers + offers2

            self.started_instances = self.buy_miners(dflop_min, offers)
        else:
            self.log_attention(f"Skip buying - enough allocated GPUs: '{self.get_total_gpus()}'")

        self.log_attention("Done!")


    def handle_problematic_instances(self):
        self.log_attention("Handle problem instances...")

        all_instances = self.get_vast_instances()
        self.handle_low_performing_instances(all_instances, HASH_PER_USD_MIN)

        self.log_attention("Done!")


    def purge_instances(self):
        self.log_attention("Purge underperforming instances...")

        instances = self.get_vast_instances()
        VastMinerRealtimeTable(instances).print_table()

        self.kill_outbid_instances(instances)

        for inst in instances:
            hpd: int = inst.hashrate_per_dollar()

            if inst.is_miner_online() and inst.hashrate() < 444:
                print(f"Kill instance {inst.machine_id} due to Hashrate is zero ({inst.hashrate()})")
#                offer_id = OfferMap().get(inst.cid)
#                VastOfferRepo().put(offer_id, True)
#                self.kill_instance(inst)

            elif (hpd > 1) and (hpd < HASH_PER_USD_MIN):
                print(f"Killing instance due to Hashrate Per USD below minimum: {hpd}")
#                self.kill_instance(inst)

            elif hpd > 220000:
                print(f"Killing instance due to Hashrate Per USD above minimum: {hpd}")
#                self.kill_instance(inst)

        self.log_attention("Done!")


    def kill_outbid_instances(self, instances: list):
        self.log_attention("Kill outbid instances...")

        for inst in instances:
            delete = False

            #  This case shouldn't happen but it still does!!!
            #  My bid is lower than the min bid offered on the market place
            #  but I still don't own the instance. So I will delete my bid
            if inst.is_outbid() and (inst.flops_per_dphtotal < (inst.dflop_for_min_bid() - 4)):
                log.error(f"Suspicious instance, will be deleted: {inst.cid}")
                delete = True

            elif (inst.dflop_for_min_bid() < DFLOP_KEEP):
                self.log_attention(f"Stopping id={inst.cid} due to outbid:  Instance DFLOP min bid: {int(inst.dflop_for_min_bid())}")
                delete = True
                self.vast_cache.put_offer_last_bought(inst.machine_id, int(datetime.now().timestamp()))

            if delete:
                self.kill_instance(inst)

        self.log_attention("Done!")


    def kill_instances(self, instances: list):
        for inst in instances:
            self.kill_instance(inst)


    def kill_instance(self, inst: VastInstance):
        self.vast.kill_instance(inst.cid)


    def reboot_instances(self):
        all_instances = self.get_vast_instances()

        for inst in all_instances:
            self.reboot(inst)


    def reboot(self, inst: VastInstance):

        if inst.is_running():
            self.log_attention(f"Rebooting id={inst.cid}!")
            self.vast.reboot_instance(inst.cid)
            inst.last_rebooted = datetime.now().timestamp()


    def reboot_miner_group(self, mg: MinerGroup):
        now = int(datetime.now().timestamp())

        for inst in mg.instances:
            next_reboot = datetime.fromtimestamp(inst.last_rebooted) + timedelta(minutes=45)
            if inst.is_running() and now > next_reboot.timestamp():
#                self.reboot(inst)
                pass
            else:
                self.log_attention(f"Next reboot = {next_reboot}")


    def handle_low_performing_instances(self, instances: list, hash_per_usd_min: int):
        self.log_attention("Handle low performing instances...")

        for inst in instances:
            hpg: int = inst.hashrate_per_gpu()
            hpd: int = inst.hashrate_per_dollar()
            effect = int(inst.gpu_effect) if inst.gpu_effect else 0

            # Sometimes miner doesn't start up directly - can be solved by re-starting the instance
            if inst.is_miner_online() and hpd <= 0:
#                print_attention(f"Stopping cid={inst.cid} due to: hashrate is zero")
#                print(f"Rebooting due to Hashrate is zero ({hpd})")
#                self.reboot(inst)
                pass

            elif not inst.is_running():
                pass

            elif effect < 30:
                print(f"Rebooting due to gpu effect={effect}")
#                self.reboot(inst)

            # Reboot if hashrate is low (but not zero which means there is no miner stats available)
            elif (hpg > 1) and (hpg < MIN_HASH_PER_GPU):
                print(f"Rebooting due to Hashrate per gpu={hpg}")
#                self.reboot(inst)

            elif (hpd > 1) and (hpd < hash_per_usd_min):
                print(f"Rebooting due to Hashrate per dollar={hpd}")
#                self.reboot(inst)

        miner_group_table = MinerPerformanceTable(self.vast_cache)
        miner_group_table.print()

        now = int(datetime.now().timestamp())
        balances = get_balances(now, 1.0, 1.1)
        min_effect = 41.0

        if not balances:
            return

        for mg in miner_group_table.miner_groups:
            if mg.id.lower() == config.ADDR.lower():
                wallet_balances = balances.get_for_addr(mg.id)
                delta: XenBlocksWallet = mg.balance.difference(wallet_balances)
                effect: float = calc_effect(mg.active_gpus, delta.block_per_hour())
                if 0 <= effect < min_effect:
                    print(f"Rebooting miner group due to low effect: {int(effect)} %")
                    self.reboot_miner_group(mg)
                else:
                    print(f"Miner group effect: {effect}%")
                    print(f"Delta block: {delta.block}")


    def kill_unable_to_start_instances(self, instances: list):
        self.log_attention("Kill instances unable to start...")

        to_kill = []

        for inst in instances:

            if inst.actual_status == "created" or inst.actual_status == "loading":
                self.log_attention(f"Stopping id={inst.cid} due to: Not started!")
                to_kill.append(inst)
        #                self.kill_instance(inst)

        self.kill_instances(to_kill)
        self.log_attention("Done!")


    def buy_miners(self, dflop_min: int, offers: list) -> list:
        bought_instances = []

        if len(offers) == 0:
            print(Field.attention(f"No offers above required flops per dph found: {dflop_min}"))
        else:
            for offer in offers:
                print(f"Compute Cap: {offer.compute_cap}, CUDA max: {offer.cuda_max}, Dflops: {offer.flops_per_dphtotal}, M-ID: {offer.machine_id}")

                #                        best_offer: VastOffer = offers
                # Increase bid price
                price: float = offer.min_bid
                price = price * 1.01

                if offer.flops_per_dphtotal > dflop_min:
                    created_id = self.buy_offer(offer, price)
                    if created_id > 0:
                        bought_instances.append(created_id)

                if len(bought_instances) > 8:
                    return bought_instances

        return bought_instances


    def buy_offer(self, offer: VastOffer, price: float) -> int:
        last_bought: int = self.vast_cache.get_offer_last_bought(offer.machine_id)

        diff_seconds: int = int(datetime.now().timestamp()) - last_bought

        if diff_seconds < 45*60:
            print(Field.attention(f"Bad offer: {offer.id}. Will not buy!!!"))
            return 0
        else:
            print(Field.attention(f"Creating offer id: {offer.id}"))
            contract_id = self.vast.create_instance(config.ADDR, offer.id, price, self.template)
            return contract_id

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
                self.log_attention(f"Increased bid for: {inst.cid}")
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

        return instance.dflop_for_min_bid() > DFLOP_MIN_BID and instance.is_outbid()


    def get_vast_instances2(self) -> VastMinerRealtimeTable:
        instances: list = self.vast_cache.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.load_miner_data(instances)

        return VastMinerRealtimeTable(instances)


    def get_vast_instances(self) -> list:
        instances = self.vast_cache.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.load_miner_data(instances)
        return instances


    def is_managed_instance(self, instance: VastInstance):
#        return True
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


def sort_on_dflop(instances: list):
    sorted(instances, key=dflop, reverse=True)


f = Field(ORANGE)
fgray = Field(GRAY)


def _get_next_state_event(minutes: int):
    return datetime.now() + timedelta(minutes=minutes)


