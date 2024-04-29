
from tostring import *

import copy


@auto_str
class XenBlocksWallet:
    def __init__(self, addr: str, rank: int, block: int, sup: int, xuni: int, timestamp: float, cost_ph: float):

        self.addr: str = addr
        self.rank: int = rank
        self.block: int = block
        self.sup: int = sup
        self.xuni: int = xuni

        self.timestamp_s: float = timestamp
        self.cost_per_hour: float = round(cost_ph, 3)


    def clone(self):
        return copy.copy(self)
