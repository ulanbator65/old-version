

import requests
from db.DbCache import DbCache
from VastBalanceCache import VastBalanceCache
from VastInstanceCache import VastInstanceCache
from VastInstance import VastInstance
from VastClient import VastClient

import logger as log


class VastCache:
    def __init__(self, vast: VastClient):
        self.vast = vast


    def get_balance(self) -> float:
        cache = VastBalanceCache(self.vast)
        return DbCache().get_entity(cache)


    def get_instances(self) -> list[VastInstance]:
        instances = []
        try:
            cache = VastInstanceCache(self.vast)
            data: dict = DbCache().get_entity(cache)
            rows = data.get('instances', [])

            for json_data in rows:
                inst = VastInstance(json_data)
                instances.append(inst)

        except requests.RequestException as e:
            log.error(f"Error fetching instances: {e}")

        return instances


    def get_selected_instances(self, ids: list[int]) -> list[VastInstance]:
        instances = self.get_instances()
        iterator = filter(lambda x: x.cid in ids, instances)
        result = list(iterator)
        return result

