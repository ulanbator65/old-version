

from db.AbstractCache import AbstractCache


TTL_S = 3*60*60
PREFIX = "bad_offer:"


class VastOfferCache(AbstractCache):
    def __init__(self, offer_id: int):
        self.offer_id = offer_id

    def get_ttl_s(self) -> int:
        return TTL_S


    def get_key(self) -> str:
        return PREFIX + str(self.offer_id)


    def get_entity(self) -> int:
        return 0


    def entity_to_string(self, timestamp: int):
        return str(timestamp)


    def string_to_entity(self, value: str) -> int:
        return int(value)
