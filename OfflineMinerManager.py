
from datetime import datetime, timedelta

from VastClient import VastClient
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from statemachine.State import State
from statemachine.StateMachine import StateMachine
import logger as log


S_STARTED = "Offline Miner Manager - waiting to reboot"
S_REBOOT = "Offline Miner Manager - rebooted!"

FREQUENCY_M = 50 + 60

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
#                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                   #                   "0xd9007A12b33b699Ee01B7D6f9D9fEae42AB5145C".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]


class OfflineMinerManager:

    def __init__(self, vast: VastClient, theme: int = 1):
        self.vast = vast
        self.db = XenBlocksWalletHistoryRepo()
        self.next_trigger = get_next_trigger()
        self.s_started = State(S_STARTED, [f"Reboot frequency: {FREQUENCY_M} minutes"], self.state_started)
        self.s_reboot = State(S_REBOOT, [], self.state_reboot)
        self.sm = StateMachine("Offline Miner Manager", [self.s_started, self.s_reboot], theme)


    def get_state_machine(self):
        return self.sm


    def state_started(self, time_tick: datetime) -> State:
        log.info("Next reboot at: " + str(self.next_trigger)[11:19])
        return self.get_next_state(time_tick)


    def state_reboot(self, time_tick: datetime) -> State:
        log.warning("Reboot instances...")

        all_instances = self.vast.get_instances()

        for inst in all_instances:

            if inst.is_running() and inst.addr.lower() in addr_list:
                log.info(f"Rebooting id={inst.id}!")
                self.vast.reboot_instance(inst.id)

        log.warning("Done!")

        return self.get_next_state(time_tick)


    def get_next_state(self, time_tick: datetime):
        state: State = self.sm.state

        # Started
        if state == self.s_started:
            if time_tick.timestamp() > self.next_trigger.timestamp():
                self.next_trigger = get_next_trigger()
                return self.s_reboot

        # Reboot Miners
        elif state == self.s_reboot:
            return self.s_started

        return state


    def test(self):
        all_instances = self.vast.get_instances()

        for inst in all_instances:

            if inst.is_running() and inst.addr.lower() in addr_list:
                log.info(f"Rebooting id={inst.id}!")


def get_next_trigger():
    return datetime.now() + timedelta(hours=1, minutes=50)
