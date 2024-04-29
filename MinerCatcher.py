
import time

from Automation import Automation
from VastInstance import *
from VastClient import *
from VastOffer import VastOffer
import config
from Field import *
from Menu import Menu
from BuyMenu import BuyMenu
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

        while True:
            self.catch_miners(500)

            time.sleep(1*60)
            VastMinerTable(self.get_vast_instances()).print_table()

            #            self.increase_bid()
            time.sleep(5*60)



    def catch_miners(self, dflop_min):

        offers: list[VastOffer] = self.automation.offers_A5000(dflop_min)


        if len(offers) == 0:
            print(Field.attention(f"No offers below required flops per dph found: {dflop_min}"))
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
                else:
                    print(Field.attention(f"No offers below required flops per dph found: {dflop_min}"))
                    print(Field.attention(f"Best offer was: {offer.flops_per_dphtotal}"))


    def increase_bid(self):
        self.set_state("Increase Bid Price...")

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
