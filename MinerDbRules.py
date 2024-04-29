
from MinerStatistics import MinerStatistics
from XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo


class MinerDbRules:
    def __init__(self, db: XenBlocksWalletHistoryRepo):
        self.db = db

    def should_save_to_db(self, id: str, timestamp_s):
        latest = self.db.get_latest_version(id)
        t1: int = int(timestamp_s / (3*60))
        t2: int = int(latest.timestamp_s / (3*60))
        print("t1: ", t1)
        print("t2: ", t1)
        return t2 > t1
