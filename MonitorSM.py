
from datetime import datetime, timedelta

from VastClient import VastClient
from db.HistoryManager import HistoryManager
from VastCache import VastCache
from MinerHistoryTable import MinerHistoryTable
from statemachine.State import State
from statemachine.StateMachine import StateMachine
import logger as log
import config


S_STARTED = "Show statistics"
S_DONE = "Waiting..."

FREQUENCY_M = 9

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]


class MonitorSM:

    def __init__(self, vast: VastClient, history: HistoryManager, theme: int = 1):
        self.vast_cache = VastCache(vast)
        self.history_db = history
        self.miner_group_table = MinerHistoryTable(self.vast_cache)
        self.next_trigger = _get_next_event(FREQUENCY_M)
        self.s_show_statistics = State(S_STARTED,
                                       [f"Monitor freqency {FREQUENCY_M} minutes"],
                                       self.state_show_statistics)
        self.s_completed = State(S_DONE, [], self.state_completed)
        self.sm = StateMachine("Monitor Miner Performance", [self.s_show_statistics, self.s_completed], theme)


    def get_state_machine(self):
        return self.sm


    def state_show_statistics(self, time_tick: datetime) -> State:

        self.miner_group_table.print()

        return self.s_completed


    def state_completed(self, time_tick: datetime) -> State:
        # Next trigger
        if time_tick.timestamp() > self.next_trigger.timestamp():
            self.next_trigger = _get_next_event(FREQUENCY_M)
            return self.s_show_statistics
        else:
            return self.s_completed


def _get_next_event(minutes: int):
    return datetime.now() + timedelta(minutes=minutes)
