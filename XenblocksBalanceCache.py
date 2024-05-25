
from db.AbstractCache import AbstractCache
from XenBlocks import XenBlocks


TTL_S = 60


class XenblocksBalanceCache(AbstractCache):
    def __init__(self, addr: str):
        self.addr = addr.lower()


    def get_ttl_s(self) -> int:
        return TTL_S


    def get_key(self) -> str:
        return self.addr


    def get_entity(self) -> int:
        return XenBlocks().get_balance(self.addr)


    def entity_to_string(self, entity: int):
        return str(entity)


    def string_to_entity(self, value: str) -> int:
        return int(value)

