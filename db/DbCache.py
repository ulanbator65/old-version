
from datetime import datetime
from sqlite3 import Connection

from typing import Type
from db.DbManager import DbManager
from db.AbstractCache import AbstractCache
from config import CACHE_DB
import logger as log


INSERT = "INSERT INTO cache VALUES(?, ?, ?)"
UPDATE = "UPDATE cache SET timestamp=?, value=?  WHERE key=?"
SELECT = "SELECT * FROM cache WHERE key = ?"
DELETE = "DELETE FROM cache WHERE key = ?"
CREATE_TABLE = "CREATE TABLE IF NOT EXISTS cache (key STRING PRIMARY KEY, timestamp STRING, value STRING)"


class DbCache:
    def __init__(self, db_man: DbManager = DbManager(CACHE_DB)):
        self.db: DbManager = db_man
        self.connection: Connection = None
        self.db.execute(CREATE_TABLE)


    def get_entity(self, cache: AbstractCache):
        cache_entry: DbCache.CacheEntry = self.get(cache.get_key())

        if cache_entry and cache_entry.value:
            if cache_entry.is_expired(cache.get_ttl_s()):

                data = cache.get_entity()
#                log.warning(f"Get data: {data}")
                DbCache().update(cache.get_key(), cache.entity_to_string(data))
                return data

#            log.info(f"Loaded cache: {cache_entry.value}")
            return cache.string_to_entity(cache_entry.value)

        else:
            data = cache.get_entity()

#            log.warning(f"Get data: {data}")
            DbCache().update(cache.get_key(), cache.entity_to_string(data))
            return data


    def _create(self, key: str, value: str):
        params: tuple = (key, int(datetime.now().timestamp()), value)
        self.db.insert(INSERT, params)


    def update(self, key: str, value: str):
        if value == "None":
            raise Exception("WTF!!!")

        if not value:
            log.error("Cannot store value for key '{key}': value is empty!")
            return

        params: tuple = (int(datetime.now().timestamp()), value, key)

        existing_value = self.get(key)
        if not existing_value:
            self._create(key, value)
        else:
            self.db.update(UPDATE, params)


    def get(self, key: str) -> 'CacheEntry':
        params: tuple = (key,)
        result = self.db.select(SELECT, params)

        if len(result) > 1:
            print(result)
            raise Exception("WTF!!!")

        if len(result) == 0:
            return None

        return DbCache.CacheEntry(int(result[0][1]), result[0][2])


    def delete_all(self):
        self.db.execute("DELETE FROM cache")


    class CacheEntry:
        def __init__(self, timestamp_s: int, value: str):
            self.timestamp = timestamp_s
            self.value = value


        def is_expired(self, max_age_s: int) -> bool:
            age_seconds = datetime.now().timestamp() - self.timestamp
            return age_seconds > max_age_s

        def get_int_value(self) -> int:
            return int(self.value)

        def get_float_value(self) -> float:
            return float(self.value)

        def get_value(self) -> str:
            return self.value
