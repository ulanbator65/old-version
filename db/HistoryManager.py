
from datetime import datetime
from typing import Optional

from XenBlocksWallet import XenBlocksWallet
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from db.VastBalanceHistoryRepo import VastBalanceHistoryRepo
from HistoricalBalances import HistoricalBalances
import logger as log


class HistoryManager:

    def __init__(self):
        self.wallet_db = XenBlocksWalletHistoryRepo()
        self.vast_balance_db = VastBalanceHistoryRepo()


    def save_balance(self, balances: HistoricalBalances):
        for b in balances.wallet_balances:
            b.timestamp_s = balances.timestamp
            self.wallet_db.create(b)

        self.vast_balance_db.create(balances.timestamp, balances.vast_balance)

        b = self.vast_balance_db.get(balances.timestamp)
        if b != balances.vast_balance:
            raise Exception("DB error!!")


    def get_balances(self, timestamp: int) -> Optional[HistoricalBalances]:

        vast_balance = self.get_vast_balance(timestamp)
        if not vast_balance:
            error = f"VAST balance not found: {timestamp:.0f}"
            log.info(error)
            return None

        actual_timestamp = vast_balance[0]
        balance = vast_balance[1]

        diff = (actual_timestamp - timestamp) / 3600
        if abs(diff) > 0.8:
            error = f"Diff was too high: {diff:.2f}"
            log.info(error)
            return None

        wallet_balances = self.get_wallet_balances(actual_timestamp)
        if len(wallet_balances) == 0:
            error = f"XenBlocks balances not found: {actual_timestamp:.0f}"
            log.error(error)
            return None

        return HistoricalBalances(actual_timestamp, balance, wallet_balances)


    def get_balances_with_fallback(self, timestamp: int, fallback_timestamp: int) -> Optional[HistoricalBalances]:

        vast_balance = self.get_vast_balance(timestamp)
        if not vast_balance:
            vast_balance = self.get_vast_balance(fallback_timestamp)
            msg = f"VAST balance not found: {timestamp:.0f}"
            log.info(msg)

        if not vast_balance:
            error = f"VAST balance not found for fallback: {fallback_timestamp:.0f}"
            log.warning(error)
            return None

        found_timestamp = vast_balance[0]
        balance = vast_balance[1]

        wallet_balances = self.get_wallet_balances(found_timestamp)
        if len(wallet_balances) == 0:
            error = f"  XenBlocks balances not found: {found_timestamp:.0f}"
            log.error(error)
            return None

        return HistoricalBalances(found_timestamp, balance, wallet_balances)


    def get_wallet_balances(self, timestamp_s: int) -> list:

        return self.wallet_db.get_for_timestamp(timestamp_s)


    def get_vast_balance(self, timestamp: int) -> Optional[tuple]:
        all_balances = VastBalanceHistoryRepo().get_from_timestamp(timestamp - 25*60)

        row_count = len(all_balances)
        if row_count < 1:
            return None

        balance = all_balances[row_count - 1]
        found_timestamp = balance[0]

        best_diff: float = 99999999.9
        best_balance = None

        for b in all_balances:
            found_timestamp = b[0]
            diff: float = (found_timestamp - timestamp) / 3600

            if diff < best_diff:
                best_diff = diff
                best_balance = b

        if abs(best_diff) > 0.8:
            error = f"Diff was too high: {best_diff:.2f}"
            log.info(error)
            return None

        return best_balance


    def cleanup_db(self):
        vast_balances: list = self.vast_balance_db.get_all()

        for b in vast_balances:
            wallet_balances = XenBlocksWalletHistoryRepo().get_for_timestamp(b[0])

            if not wallet_balances or len(wallet_balances) == 0:
                self.vast_balance_db.delete(b[0])
                print("Successfully deleted VAST balance: ", b)

            else:
                count = get_total_block_balance(wallet_balances)
                if count == 0:
                    self.vast_balance_db.delete(b[0])
                    print("Successfully deleted VAST balance: ", b)


def get_total_block_balance(balances: list) -> int:
    block = 0
    for b in balances:
        block += b.block

    return block
