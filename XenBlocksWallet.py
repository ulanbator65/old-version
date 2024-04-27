
from tostring import *
from MinerStatisticsRepo import *
from constants import *
from Time import Time
from MinerRules import *
import copy


@auto_str
class XenBlocksWallet:
    def __init__(self, addr: str, rank: int, block: int, sup: int, xuni: int, timestamp: float, cost_ph: float):

        self.addr = addr
        self.rank = rank
        self.block: int = block
        self.super: int = sup
        self.xuni: int = xuni

        self.timestamp_s: float = timestamp
        self.cost_per_hour: float = round(cost_ph, 3)


