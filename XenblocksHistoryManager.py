
import time
from datetime import datetime

from Automation import Automation
import XenBlocksCache as XenBlocks
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from statemachine.State import State
from statemachine.StateMachine import StateMachine
import config
from Field import *
from Menu import Menu
import logger as log


f = Field(ORANGE)
fgray = Field(GRAY)

S_STARTED = "Waiting to save Xenblocks history..."
S_DONE = "Xenblocks history saved successfully!"

SAVE_HISTORY_M = 11

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                   #                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                   #                   "0xd9007A12b33b699Ee01B7D6f9D9fEae42AB5145C".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]


class XenblocksHistoryManager:

    def __init__(self):
        self.db = XenBlocksWalletHistoryRepo()
        self.state: str = None
        self.s1 = State(S_STARTED, [f"At minutes after the hour: {SAVE_HISTORY_M}"], self.state_started)
        self.s2 = State(S_DONE, [], self.state_completed)
        self.sm = StateMachine([self.s1, self.s2])


    def get_state_machine(self):
        return self.sm


    def state_started(self, time_tick: datetime) -> State:

        if time_tick.timetuple().tm_min > SAVE_HISTORY_M:
            timestamp = int(time_tick.timestamp())

            result = False
            for addr in addr_list:
                snapshot = XenBlocks.get_wallet_balance(addr, timestamp)
                if snapshot:
                    log.print_info("Saving snapshot: " + snapshot.addr)
                    result = self.db.create(snapshot)

            if result and result is True:
                return self.s2
#                self.set_state(S_DONE)

        return self.s1


    def state_completed(self, time_tick: datetime) -> State:

        if time_tick.timetuple().tm_min < SAVE_HISTORY_M:
            return self.s1
#            self.set_state(S_STARTED, [f"Configured minutes: {FREQUENCY_M}"])
        else:
            return self.s2


def print_attention(info: str):
    print(f.format(info))
