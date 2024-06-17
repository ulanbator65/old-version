

from db.AbstractCache import AbstractCache
from db.DbCache import DbCache

TTL_S = 30
PREFIX = "offer_map:"


class OfferMap:

    def get(self, instance_id: int) -> int:
        key = self._get_key(instance_id)
        cach_entry: DbCache.CacheEntry = DbCache().get(key)
        if not cach_entry:
            return 0

        return int(cach_entry.value)


    def put(self, contract_id: int, offer_id: int):
        key = self._get_key(contract_id)
        DbCache().update(key, str(offer_id))


    def _get_key(self, instance_id: int) -> str:
        return PREFIX + str(instance_id)

