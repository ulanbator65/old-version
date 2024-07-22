
from db.AbstractCache import AbstractCache
from db.DbCache import DbCache
import time


TTL_S = 60
KEY = "cache_lock"
UNLOCKED_ID = "0"


class CacheLock(AbstractCache):


    def aquire_lock(self, ident: str):
        while self._is_locked():
            time.sleep(5)

        DbCache().update(self.get_key(), ident)
        print("Aquired cache lock for id: ", ident)


    def release_lock(self):
        DbCache().update(self.get_key(), UNLOCKED_ID)


    def _is_locked(self):
        ident: int = DbCache().get_entity(self)
        return ident != UNLOCKED_ID


    def get_ttl_s(self) -> int:
        return TTL_S


    def get_key(self) -> str:
        return KEY


    def get_entity(self) -> str:
        return UNLOCKED_ID


    def entity_to_string(self, entity: str):
        return entity


    def string_to_entity(self, value: str) -> str:
        return value

