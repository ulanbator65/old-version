
from datetime import datetime
from statemachine.State import State
from Menu import Menu
import logger as log
from constants import *


class StateMachine:

    def __init__(self, states: list[State]):
        self.states: list[State] = states
        self.next_state: State = self.states[0]
        print_state(self.next_state)


    def execute(self, time_tick: datetime):
        s = self.next_state.execute(time_tick)

        if s.name != self.next_state.name:
            print(self.next_state.name, " ==>> ", s.name)
            print_state(s)

        self.next_state = s


def print_state(state: State):
    add_offset = lambda x: " "*5 + x
    offset_rows = list(map(add_offset, state.info))

    Menu(state.name, [""] + offset_rows, 60, col_header=GOLD, col_row=GRAY, col_bg=BG_GRAY).center().print()
    print()
