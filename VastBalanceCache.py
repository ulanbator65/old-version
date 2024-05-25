
from db.AbstractCache import AbstractCache
from XenBlocks import XenBlocks
from VastClient import VastClient



TTL_S = 60
KEY = "VastBalance"


class VastBalanceCache(AbstractCache):
    def __init__(self, vast: VastClient):
        self.vast = vast


    def get_ttl_s(self) -> int:
        return TTL_S


    def get_key(self) -> str:
        return KEY


    def get_entity(self) -> float:
        return self.vast.get_vast_balance()


    def entity_to_string(self, entity: float):
        return str(entity)


    def string_to_entity(self, value: str) -> float:
        return float(value)

