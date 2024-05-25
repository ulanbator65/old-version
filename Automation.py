
from VastClient import *
from VastCache import VastCache
from VastOffer import VastOffer
import config
from Field import *

A5000_dflops_premium = 500
A5000_dflops_high = 240


class Automation:
    def __init__(self, vast):
        self.vast: VastClient = vast
        self.vast_cache = VastCache(vast)


    def kill_problematic_instances(self):
        print("Purge problematic instances...")
        all = self.vast_cache.get_instances()
        selected = list(filter(lambda x: x.addr and x.addr.lower() == config.ADDR.lower(), all))

        for inst in selected:
            if (inst.actual_status == "created"):
                if "A40" in inst.gpu_name:
                    self.vast.kill_instance(inst.id)


    def kill_all_running_instances(self):
        print("Kill running...")
        all = self.vast_cache.get_instances()
        selected = list(filter(lambda x: x.addr and x.addr.lower() == config.ADDR.lower(), all))

        for inst in selected:
#            if inst.is_running() or (inst.actual_status == "created"):
            if "A40" in inst.gpu_name:
                self.vast.kill_instance(inst.id)


    def runBot(self):
#        offers: list = self.offers_A40()
        offers: list = self.offers_A5000()

        if len(offers) > 0:
            best_offer: VastOffer = offers[0]
            price: float = best_offer.min_bid
            # Increase bid price
            price = price * 1.02

            if best_offer.flops_per_dphtotal > A5000_dflops_premium:
                self.vast.create_instance(config.ADDR, best_offer.id, price)
            else:
                print(Field.attention(f"No offers above required flops per dph found: {A5000_dflops_premium}"))
                print(Field.attention(f"Best offer was: {best_offer.flops_per_dphtotal}"))


    def runBot2(self):
        top_offers: list = self.offers_A40()

        if len(top_offers) > 0:
            self.__create_instance(top_offers[0])
        else:
            print("No offers found currently, try again later.")


    def increase_bid(self, instances: list, dflop_min: int, bid_factor=1.02):
        for inst in instances:
            self.increase_bid_for_instance(inst, dflop_min, bid_factor)


    def increase_bid_for_instance(self, inst: VastInstance, dflop_min: int, bid_factor=1.02):
        if inst.is_outbid() and inst.dflop_for_min_bid() > dflop_min:

            price = inst.cost_per_hour * bid_factor
            # Faster bid rate at higher DFLOPs
            if inst.flops_per_dphtotal > 900:
                price = inst.cost_per_hour * 1.08

            print("Found outbid instance: ", inst.id)
            print("Current Price: ", inst.cost_per_hour)
            print("Current DFLOP: ", inst.flops_per_dphtotal)
            print("Bid Price: ", inst.min_bid)
            print("Bid DFLOP: ", inst.dflop_for_min_bid())
            print("Adjusted Price: ", price)
            self.vast.increase_bid(inst.id, price)
        else:
            print(f"Is outbid: {inst.is_outbid()}")
            print(f"Bid DFLOP:  {inst.dflop_for_min_bid()}")


    def offers_30_series(self) -> list[VastOffer]:
        query1 = VastQuery.gpu_model_query("RTX_3060")
        query1.max_bid = 0.6
        query1.tflop_price = 350.0

        query2 = VastQuery.gpu_model_query("RTX_3090")
        query2.max_bid = 0.6
        query2.tflop_price = 350.0

        offers = self.__get_top_offers([query1, query2])
        return self.sort_offers('flops_per_dphtotal', offers)[:40]


    def offers_A40(self, dflop=220) -> list[VastOffer]:
        query = VastQuery.gpu_model_query("A40")
        query.max_bid = 0.99
#        query.tflop_price = dflop

        return self.get_top_offers(query)


    def selectTopOffersA4000(self) -> list[VastOffer]:
        query = VastQuery.gpu_model_query("RTX_A4000")
        query.max_result = 10
        query.min_gpus = 8
        query.max_bid = 0.5
        query.tflop_price = 199

        return self.get_top_offers(query)


    def offers_A5000(self, dflop_min: int = 0) -> list[VastOffer]:
        query = VastQuery.gpu_model_query("RTX_A5000")
        query.max_result = 10
        query.max_bid = 0.99
#        query.tflop_price = dflop_min

        return self.get_top_offers(query)


    def offers_A4000(self) -> list[VastOffer]:
        query = VastQuery.gpu_model_query("RTX_A4000")
        query.max_result = 10
        query.max_bid = 0.99
        return self.get_top_offers(query)


    def get_top_offers(self, query: VastQuery) -> list[VastOffer]:
        top_offers = self.vast.get_offers(query)

        return self.sort_offers('flops_per_dphtotal', top_offers)[:query.max_result]


    def sort_offers(self, column: str, offers: list[VastOffer]):
        column = 'flops_per_dphtotal'
        return sorted(offers, key=lambda x: float(x.get(column, float('inf'))), reverse=True)


    def selectTopOffers_tflop_price(self):
        query = VastQuery.tflop_price_query(599.9)
        query.max_result = 4
        query.min_gpus = 4
        query.max_bid = 0.4
#        query.gpu_models = ["RTX_4090"]
        Max = lambda instance: instance if (instance['Link'].contains("fiber1.kmidata.es")) else True

        query.filter = Max

        return self.get_top_offers(query)


    def selectTopOffersA5000_8(self) -> list:
        query = VastQuery.gpu_model_query("RTX_A5000")
        query.max_result = 10
        query.min_gpus = 8
        query.max_bid = 0.61
        query.location = "Pennsylvania"

        return self.get_top_offers(query)


    def allocate_whitelist(self):
        # Allocate from Whitelist
        if len(config.WHITELIST) == 0:
            print("No offers found currently, try again later.")
            return

        whitelist = config.WHITELIST
#        whitelist = [10373279]
        query = VastQuery.max_bid_query(1.9)

        offers = self.vast.get_offers(query)
        offer = None

        for off in offers:
            iterator = filter(lambda x: (off.get('id') == x), whitelist)
            offer = list(iterator)
            if len(offer) > 0:
                break

        print("xxxxxx", len(offers))
        print("xxxxxx", offer)
        if len(offer) == 0:
            print("No offers found currently, try again later.")



    def select_top_offers_A4000_8(self):
        query = VastQuery.gpu_model_query("RTX_A4000")
        query.gpu_models.append("RTX_A40")
        query.max_result = 10
        query.min_gpus = 8
        query.max_bid = 0.61
        query.location = "Pennsylvania"

        return self.get_top_offers(query)


    def selectTopOffersA4000_4(self):
        query = VastQuery.gpu_model_query("RTX_A4000")
        query.max_result = 10
        query.min_gpus = 4
        query.max_bid = 0.3

        return self.get_top_offers(query)


    def selectTopOffersA4000_2(self):
        query = VastQuery.gpu_model_query("RTX_A4000")
        query.max_result = 10
        query.min_gpus = 2
        query.max_bid = 0.06

        return self.get_top_offers(query)


    def __get_top_offers(self, queries: list):
        offers = []
        for query in queries:
            offers += self.get_top_offers(query)
            print(len(offers), ", ")

        return offers


    def __create_instance(self, offer):
        bid_factor = 1.0 + (config.BID_INCREASE_PCT / 100)
        price = offer.get('dph_total') * bid_factor

        print("Price: ", offer.get('dph_total'))
        print("Adjusted Price: ", price)

        return self.vast.create_instance(config.ADDR, offer.id, price)



def is_white_listed(id) -> bool:
    if id in config.WHITELIST:
        return True
    else:
        return False

