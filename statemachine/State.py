

from datetime import datetime
import logger as log



class State:

    def __init__(self, name: str, info: list[str], runnable):
        self.name = name
        self.info = info
        self.runnable = runnable


    def execute(self, time_tick: datetime) -> 'State':
        return self.runnable(time_tick)


