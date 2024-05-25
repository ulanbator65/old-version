


class AbstractCache:


    def get_ttl_s(self) -> int:
        return 0


    def get_key(self) -> str:
        return ""


    def get_entity(self):
        return None


    def entity_to_string(self, entity):
        return ""


    def string_to_entity(self, value: str):
        return None
