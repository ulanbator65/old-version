
from db.AbstractCache import AbstractCache
from VastClient import VastClient
import json


TTL_S = 20
KEY = "VastInstances"


class VastInstanceCache(AbstractCache):
    def __init__(self, vast: VastClient):
        self.vast = vast


    def get_ttl_s(self) -> int:
        return TTL_S


    def get_key(self) -> str:
        return KEY


    def get_entity(self) -> dict:
        response = self.vast.get_cached_response()
        return self.string_to_entity(response.text)


    def entity_to_string(self, entity: dict):
        return json.dumps(entity)


    def string_to_entity(self, value: str) -> dict:
        return json.loads(value)

