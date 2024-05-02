
from tostring import *


@auto_str
class XenBlocksWallet:
    def __init__(self, addr: str, rank: int, block: int, sup: int, xuni: int, timestamp: float, cost_ph: float):

        self.addr: str = addr
        self.rank: int = rank
        self.block: int = block
        self.sup: int = sup
        self.xuni: int = xuni

        self.timestamp_s: int = int(timestamp)
        self.cost_per_hour: float = round(cost_ph, 3)


    def difference(self, other_wallet: 'XenBlocksWallet') -> 'XenBlocksWallet':
        drank: int = self.rank - other_wallet.rank
        dblock: int = self.block - other_wallet.block
        dsup: int = self.sup - other_wallet.sup
        dxuni: int = self.xuni - other_wallet.xuni

        # Workaround for XenBlocks sometimes dropping super count
        dsup = dsup if dsup > 0 else 0

        timestamp_s = self.timestamp_s - other_wallet.timestamp_s
        cost_per_hour = (self.cost_per_hour + other_wallet.cost_per_hour) / 2

        return XenBlocksWallet(self.addr, drank, dblock, dsup, dxuni, timestamp_s, cost_per_hour)
