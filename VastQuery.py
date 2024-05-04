
from tostring import auto_str
from Field import Field
from constants import *

f: Field = Field(DARK_PINK)


@auto_str
class VastQuery:

    def __init__(self, min_gpus, gpu_model = None):
        self.min_gpus = min_gpus
        self.gpu_model = gpu_model
        self.max_bid = 0.0
        self.max_result = 200
        self.tflop_price = 0.0
        #'flops_per_dphtotal'
        self.price_increase_factor = 1.0
        self.location = ''
        self.verified = True


    @staticmethod
    def gpu_model_query(gpu_model: str):
        return VastQuery(0, gpu_model)

    @staticmethod
    def tflop_price_query(tflop_price):
        q = VastQuery(0)
        q.tflop_price = tflop_price
        return q

    @staticmethod
    def max_bid_query(max_bid: float):
        q = VastQuery(0)
        q.max_bid = round(max_bid, 3)
        return q


    def get_query(self) -> str:
#        query_parts = ["num_gpus>=1", "verified=false", "rented=false", f"min_bid<={self.max_bid}"]
        query_parts = []

        if self.max_bid > 0.0:
            query_parts.append(f"min_bid<={self.max_bid}")

        if self.min_gpus > 1:
            query_parts.append(f"num_gpus>={self.min_gpus}")

        if self.gpu_model:
            query_parts.append(f"gpu_name={self.gpu_model.replace(' ', '_')}")

        if self.tflop_price > 10.0:
#            pass
            query_parts.append(f"flops_usd>{self.tflop_price}")
#            query_parts.append(f"flops_per_dphtotal>{200}")

        if self.verified:
            query_parts.append("verification=verified")

        query_str = " ".join(query_parts)

        print(f.format(str(self)))
        return query_str


    def filter_instance(self, inst) -> bool:
        if self.tflop_price > 0.0 and int(inst.get('flops_per_dphtotal')) < self.tflop_price:
            return False
        return True


