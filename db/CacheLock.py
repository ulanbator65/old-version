
from db.AbstractCache import AbstractCache
from db.DbCache import DbCache
import time


TTL_S = 60
KEY = "cache_lock"


class CacheLock(AbstractCache):


    def aquire_lock(self, ident: int):
        while self._is_locked():
            time.sleep(5)

        DbCache().update(self.get_key(), str(ident))


    def release_lock(self):
        DbCache().update(self.get_key(), str(0))


    def _is_locked(self):
        ident: int = DbCache().get_entity(self)
        return ident > 0


    def get_ttl_s(self) -> int:
        return TTL_S


    def get_key(self) -> str:
        return KEY


    def get_entity(self) -> int:
        return 0


    def entity_to_string(self, entity: int):
        return str(entity)


    def string_to_entity(self, value: str) -> int:
        return int(value)

