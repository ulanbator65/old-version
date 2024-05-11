
from XenBlocksWallet import XenBlocksWallet
from tostring import *


@auto_str
class HistoricalBalances:

    def __init__(self, timestamp: int, vast_balance: float, wallet_balances: list[XenBlocksWallet] = []):
        self.vast_balance = vast_balance
        self.wallet_balances: list[XenBlocksWallet] = wallet_balances
        self.timestamp: int = timestamp


    def add_balance(self, wallet_balance: XenBlocksWallet):
        self.wallet_balances.append(wallet_balance)


    def get_for_addr(self, addr: str):
        for b in self.wallet_balances:
            if addr.lower() == b.addr.lower():
                return b

        return None


