

from datetime import datetime
from logger import *

from VastClient import VastClient
from MinerStatisticsTable import MinerStatisticsTable
from XenblocksHistoryManager import XenblocksHistoryManager
from GpuCatcher import GpuCatcher
import config

SAVE_BALANCE_M: int = 39


class Controller:

    def __init__(self, vast: VastClient):
        self.vast = vast
        self.previous_time_tick = None
        self.balance_history = MinerStatisticsTable(self.vast)
        self.xenblocks_history = XenblocksHistoryManager()
        self.gpu_catcher = GpuCatcher(config.ADDR, vast).sm


    def get_time(self) -> datetime:
        return self._time_tick()


    def _time_tick(self):
        tick = datetime.now()
        print_info(str(tick)[11:19])

        if self.previous_time_tick:
            delta = tick - self.previous_time_tick
            if delta.seconds > 2*60:
                self.handle_time_tick(tick)

        self.previous_time_tick = tick
        return tick


    def handle_time_tick(self, tick: datetime):
        self.xenblocks_history.sm.execute(tick)
        self.gpu_catcher.execute(tick)

        # Trigger update of history for XenBlocks data
#        minutes = tick.timetuple().tm_min
#        print("M: ", minutes)
#        diff = abs(SAVE_BALANCE_M - minutes)

#        if diff <= 7:
#            self.balance_history.update_balance_history(int(tick.timestamp()))
#            print("Updated balance history!")

