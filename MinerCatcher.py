
import time

from Automation import Automation
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from views.BuyMenu import BuyMenu
from VastMinerTable import VastMinerTable


f = Field(ORANGE)
fgray = Field(GRAY)

S_START_MINING = "XUNI Miner running..."
S_CREATE_MINERS = "Setup miners for XUNI..."
S_KEEP_MINING = "Just keep mining..."



class MinerCatcher:

    def __init__(self, vast):
        self.vast: VastClient = vast
        self.automation = Automation(vast)
        self.hours = 0
        self.minutes: int = 0
        self.state: str = "None"



    def catch_miners(self):
        dflops = 200

        while True:
            self.buy_miners(500)

            time.sleep(1*60)
            instances = self.get_vast_instances()
            if len(instances) > 0:
                VastMinerTable().print_table()

            #            self.increase_bid()
            time.sleep(5*60)





    def buy_miners(self, dflop_min):
        selected_models = ["RTX A2000", "RTX A4000", "RTX A5000"]
        is_model = lambda x: x.gpu_name in selected_models

        query = VastQuery.max_bid_query(0.99)  #.gpu_model_query("RTX_A5000")
#        query = VastQuery.gpu_model_query("RTX_A5000")
        query.verified = False
        query.tflop_price = dflop_min

        offers: list[VastOffer] = self.vast.get_offers(query) # automation.get_top_offers(query)
        offers = list(filter(is_model, offers))
        offers = self.automation.sort_offers('flops_per_dphtotal', offers)

#        offers: list[VastOffer] = self.automation.offers_A5000(dflop_min)

        if len(offers) == 0:
            print(Field.attention(f"No offers above required flops per dph found: {dflop_min}"))
        else:
            BuyMenu.print_offer_table(offers)

            for offer in offers:
                #                        best_offer: VastOffer = offers
                # Increase bid price
                price: float = offer.min_bid
                price = price * 1.02

                if offer.flops_per_dphtotal > dflop_min:
                    print(Field.attention(f"Creating instance: {offer.id}"))
                    self.vast.create_instance(config.ADDR, offer.id, price)


    def increase_bid(self):

        instances = self.get_vast_instances()
        outbid_instances = list(filter(lambda x: self.should_bid(x), instances))

        self.automation.increase_bid(outbid_instances, 1.04)


    def should_bid(self, instance: VastInstance):
        return instance.is_outbid() and instance.num_gpus > 2


    def get_vast_instances(self):
        instances = self.vast.get_instances()
        return list(filter(lambda x: self.is_managed_instance(x), instances))


    def is_managed_instance(self, instance: VastInstance):
        return instance.has_address(config.ADDR) and instance.is_model_a40()
