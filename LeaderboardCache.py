
from db.AbstractCache import AbstractCache
from XenBlocks import XenBlocks
from XenBlocksWallet import XenBlocksWallet


TTL_S = 2*60*60
KEY = "leaderboard"


class LeaderbordCache(AbstractCache):


    def get_ttl_s(self) -> int:
        return TTL_S


    def get_key(self) -> str:
        return KEY


    def get_entity(self) -> str:
        return XenBlocks().get_leaderboard()


    def entity_to_string(self, entity: str):
        return entity


    def string_to_entity(self, value: str) -> str:
        return value

