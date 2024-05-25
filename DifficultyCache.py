

from db.AbstractCache import AbstractCache
from XenBlocks import XenBlocks


TTL_S = 20
KEY = "difficulty"


class DifficultyCache(AbstractCache):

    def get_ttl_s(self) -> int:
        return TTL_S

    def get_key(self) -> str:
        return KEY

    def get_entity(self) -> int:
        return XenBlocks().get_difficulty()

    def entity_to_string(self, entity: int):
        return str(entity)

    def string_to_entity(self, value: str) -> int:
        return int(value)

