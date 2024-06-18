

from db.AbstractCache import AbstractCache
from XenBlocks import XenBlocks
from db.DbCache import DbCache

TTL_S = 3*60*60
PREFIX = "bad_offer:"


class VastOfferRepo:

    def get(self, offer_id: int) -> int:
        key = self._get_key(offer_id)
        cach_entry: DbCache.CacheEntry = DbCache().get(key)

        if cach_entry:
            return int(cach_entry.value)
        return 0


    def put(self, offer_id: int, timestamp: int):
        key = self._get_key(offer_id)
        DbCache().update(key, str(timestamp))


    def _get_key(self, offer_id: int) -> str:
        return PREFIX + str(offer_id)

