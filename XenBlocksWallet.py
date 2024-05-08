
from datetime import datetime


class XenBlocksWallet:
    def __init__(self, addr: str, rank: int, block: int, sup: int, xuni: int, timestamp: float, cost_ph: float):

        self.addr: str = addr
        self.rank: int = rank
        self.block: int = block
        self.sup: int = sup
        self.xuni: int = xuni
        self.timestamp_s: int = int(timestamp)
        self.cost_per_hour: float = round(cost_ph, 3)
        print("Cost: ", self.cost_per_hour)


    def to_str(self):
        time = datetime.fromtimestamp(self.timestamp_s)
        return f"addr: {self.addr[0:8]}..., time: {str(time)[11:19]}, rank: {self.rank}, block: {self.block}, super: {self.sup}"


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


    def duration_hours(self):
        return self.timestamp_s / 3600


    def block_rate(self):
        return self.block / self.duration_hours()


    def block_cost(self):
        block_rate = self.block_rate()
        return self.cost_per_hour / block_rate if block_rate > 0 else 0.0
