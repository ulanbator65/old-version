

import time
from datetime import datetime
import logger as log

from statemachine.StateMachine import StateMachine
from VastClient import VastClient


class Controller:

    def __init__(self, vast: VastClient):
        self.vast = vast
        self.previous_time_tick = None
        self.state_machines: list[StateMachine] = []


    def add_state_machine(self, sm):
        self.state_machines.append(sm)


    def run(self):
        while True:
            time_tick = datetime.now()
            log.info(str(time_tick)[11:19])

            for sm in self.state_machines:
                sm.execute(time_tick)

            time.sleep(60)


    def get_time(self) -> datetime:
        return self._time_tick()


    def _time_tick(self):
        tick = datetime.now()
        log.info(str(tick)[11:19])

#        if self.previous_time_tick:
#            delta = tick - self.previous_time_tick
#            if delta.seconds > 2*60:
#                self.handle_time_tick(tick)

        self.previous_time_tick = tick
        return tick

