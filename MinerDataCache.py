
import traceback
from datetime import datetime
import json
from db.DbCache import DbCache
from db.AbstractCache import AbstractCache
import logger as log
import requests


NULL_RESPONSE: requests.Response = None


class MinerDataCache(AbstractCache):

    def __init__(self, miner_id: int, miner_url: str):
        self.miner_id = miner_id
        self.miner_url = miner_url


    def get_miner_data(self) -> dict:
        return DbCache().get_entity(self)


    def get_ttl_s(self) -> int:
        return 30 * 60


    def get_key(self) -> str:
        return f"miner:{self.miner_id}"


    def get_entity(self) -> dict:
        response = _get_miner_statistics(self.miner_url)
        return self.string_to_entity(response.text) if response else None


    def entity_to_string(self, entity: dict) -> str:
        return json.dumps(entity)


    def string_to_entity(self, value: str) -> dict:
        return json.loads(value)


def get_miner_statistics_xxxxx(miner_id: int, miner_url: str) -> dict:
    ttl_s = 30 * 60
    key = f"miner:{miner_id}"
    cach_entry: DbCache.CacheEntry = DbCache().get(key)

    if cach_entry:
        if cach_entry.is_expired(ttl_s):
            response = _get_miner_statistics(miner_url)
            log.warning(f"Get Miner data: {response.text}")
            DbCache().update(key, response.text)
            return json.loads(response.text)

        log.info(f"Loaded Miner cache: {cach_entry.value}")
        return json.loads(cach_entry.value)

    else:
        response = _get_miner_statistics(miner_url)
        log.warning(f"Get Miner data: {response.text}")
        DbCache().update(key, response.text)
        return json.loads(response.text)


def _get_miner_statistics(miner_url: str) -> requests.Response:

    # No connection to Miner
    if not miner_url:
        log.info(f"Miner stats skipped for instance {id} due to unavailable external port.")
        return NULL_RESPONSE

    # Get Miner data
    response = requests.get(miner_url, timeout=5)
    if response.status_code == 200:
#        key: str = f"miner:{miner_id}"
#        DbCache().update(key, response.text)
        return response

    else:
        log.info(f"Failed to get miner data from {miner_url} for instance {id}: Status code {response.status_code}")
        return NULL_RESPONSE

