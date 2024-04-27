
from tostring import auto_str


@auto_str
class VastOffer:

    def __init__(self, json: dict):
        #        print(json)
        self.json: dict = json
        self.id: int = json.get('id')
        self.dph_total: float = json.get('dph_total')
        self.min_bid: float = json.get('min_bid')
        self.flops_per_dphtotal: int = int(self.json.get('flops_per_dphtotal'))


    def get(self, field: str, default=''):
        return self.json.get(field, default)


    def increase_price(self, percent: int):
        bid_factor = 1.0 + (percent / 100.0)
        print("Percent: ", bid_factor)
#        self.dph_total = self.dph_total * bid_factor
#        self.min_bid = self.min_bid * bid_factor
        return self.min_bid * bid_factor

