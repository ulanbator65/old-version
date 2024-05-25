
from datetime import datetime
from statemachine.State import State
from Menu import Menu
import logger as log
from constants import *


class StateMachine:

    def __init__(self, name: str, states: list[State], theme: int = 1):
        self.name = name
        self.states: list[State] = states
        self.state: State = self.states[0]
        self.end_state = None
        self.theme = theme
        print_state_machine(self.name, self.theme)


    def set_end_state(self, state: State):
        self.end_state = state


    def execute(self, time_tick: datetime):
        s = self.state.execute(time_tick)

        if s.name != self.state.name:
            print(self.name, ": ", self.state.name, " ==>> ", s.name)
            print_state(s, self.theme)

        self.state = s


def print_state(state: State, theme: int):
    add_offset = lambda x: " "*5 + x
    offset_rows = list(map(add_offset, state.info))

    if theme == 1:
        Menu(state.name, [""] + offset_rows, 60, col_header=GOLD, col_row=GRAY, col_bg=BG_GRAY).center().print()
    elif theme == 2:
        Menu(state.name, [""] + offset_rows, 60, col_header=LIGHT_CYAN2, col_row=GRAY, col_bg=BG_GRAY).center().print()
    else:
        Menu(state.name, [""] + offset_rows, 60, col_header=LIGHT_PINK, col_row=GRAY, col_bg=BG_GRAY).center().print()
    print()
    print()


def print_state_machine(name: str, theme: int):
    add_offset = lambda x: " "*5 + x
    offset_rows = [] # list(map(add_offset, state.info))

    if theme == 1:
        Menu(name, [""] + offset_rows, 60, col_header=GOLD, col_row=GRAY, col_bg=BG_GRAY).center().print()
    elif theme == 2:
        Menu(name, [""] + offset_rows, 60, col_header=LIGHT_CYAN2, col_row=GRAY, col_bg=BG_GRAY).center().print()
    else:
        Menu(name, [""] + offset_rows, 60, col_header=LIGHT_PINK, col_row=GRAY, col_bg=BG_GRAY).center().print()
    print()
    print()
