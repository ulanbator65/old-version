
from datetime import datetime, timedelta

import XenBlocksCache as Cache
from XenBlocksWallet import XenBlocksWallet

from VastClient import VastClient
from VastInstance import VastInstance
from db.HistoryManager import HistoryManager
from HistoricalBalances import HistoricalBalances
from statemachine.State import State
from statemachine.StateMachine import StateMachine
import logger as log
from Field import Field
import config


S_STARTED = "Xenblocks history - waiting"
S_DONE = "Xenblocks history - saved!"

FREQUENCY_M = 12

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]


class HistoryManagerSM:

    def __init__(self, vast: VastClient, history: HistoryManager, theme: int = 1):
        self.vast = vast
        self.history_db = history
        self.next_trigger = _get_next_event(FREQUENCY_M)
        self.next_reboot = _get_next_event(2 * 60)
        self.s_save_to_history = State(S_STARTED,
                                       [f"Save history freqency {FREQUENCY_M}"],
                                       self.state_save_to_history)
        self.s_completed = State(S_DONE, [], self.state_completed)
        self.sm = StateMachine("History Manager", [self.s_save_to_history, self.s_completed], theme)


    def get_state_machine(self):
        return self.sm


    def state_save_to_history(self, time_tick: datetime) -> State:

        timestamp = int(time_tick.timestamp())
        vast_balance = self.vast.get_vast_balance()

        if not vast_balance:
            # Try again later
            return self.s_save_to_history

        wallet_balances = []

        result = False
        for addr in addr_list:
            balance = Cache.get_balance(addr)

            if balance == 0:
                # Try again later
                return self.s_save_to_history

            snapshot = XenBlocksWallet(addr, 0, balance, 0, 0, timestamp, 0.0)
            wallet_balances.append(snapshot)

        balances = HistoricalBalances(timestamp, vast_balance, wallet_balances)

        log.info(f"Saving historical balances: {len(balances.wallet_balances)}")
        self.history_db.save_balance(balances)

        return self.s_completed


    def state_completed(self, time_tick: datetime) -> State:

        # Reboot VAST instances if time is right (every 2 hours)
        if time_tick.timestamp() > self.next_reboot.timestamp():
            self.next_reboot = _get_next_event(8 * 60)
            self.reboot_instances()

        # Next trigge
        if time_tick.timestamp() > self.next_trigger.timestamp():
            self.next_trigger = _get_next_event(FREQUENCY_M)
            return self.s_save_to_history
        else:
            return self.s_completed


    def reboot_instances(self):
        self.log_attention("Reboot instances...")

        all_instances = self.get_vast_instances()

        for inst in all_instances:
            self.log_attention(f"Rebooting id={inst.id}!")
            self.reboot(inst)

        self.log_attention("Done!")


    def reboot(self, inst: VastInstance):
        if inst.is_running():
            self.vast.reboot_instance(inst.id)


    def get_vast_instances(self) -> list[VastInstance]:
        instances = self.vast.get_instances()
        instances = list(filter(lambda x: self.is_managed_instance(x), instances))
        self.vast.load_miner_data(instances)
        return instances


    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR)


    def log_attention(self, info: str):
        text = self.sm.state.name + ": " + info
        print(Field.attention(text))


def _get_next_event(minutes: int):
    return datetime.now() + timedelta(minutes=minutes)
