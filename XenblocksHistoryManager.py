
from datetime import datetime, timedelta

import XenBlocksCache as Cache
from MinerHistoryTable import MinerHistoryTable
from statemachine.State import State
from statemachine.StateMachine import StateMachine
import logger as log


S_STARTED = "Xenblocks history - waiting"
S_DONE = "Xenblocks history - saved!"

FREQUENCY_M = 20

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]


class XenblocksHistoryManager:

    def __init__(self, history_table: MinerHistoryTable, theme: int = 1):
        self.history_table = history_table
        self.next_trigger = _get_next_trigger()
        self.state: str = None
        self.s_save_to_history = State(S_STARTED,
                                       [f"Save history freqency {FREQUENCY_M}"],
                                       self.state_started)
        self.s2 = State(S_DONE, [], self.state_completed)
        self.sm = StateMachine("History Manager", [self.s_save_to_history, self.s2], theme)


    def get_state_machine(self):
        return self.sm


    def state_started(self, time_tick: datetime) -> State:

        timestamp = int(time_tick.timestamp())

        result = False
        for addr in addr_list:
            snapshot = Cache.get_wallet_balance(addr, timestamp)
            if snapshot:
                log.info("Saving snapshot: " + snapshot.addr)
#                result = self.db.create(snapshot)

                result = self.history_table.save_historic_data(snapshot)

        self.history_table.print()


        if result and result is True:
            return self.s2

        return self.s_save_to_history


    def state_completed(self, time_tick: datetime) -> State:

        if time_tick.timestamp() > self.next_trigger.timestamp():
            self.next_trigger = _get_next_trigger()
            return self.s_save_to_history
        else:
            return self.s2


def _get_next_trigger():
    return datetime.now() + timedelta(minutes=20)
