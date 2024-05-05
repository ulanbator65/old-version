
import time
from datetime import datetime

from Automation import Automation, VastClient
from VastOffer import VastOffer
from statemachine.StateMachine import StateMachine, State
from Field import *
import logger as log


f = Field(ORANGE)
fgray = Field(GRAY)

S_STARTED = "Will buy cheap miner GPU's..."

FREQUENCY_M = 2

addr_list: list = ["0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a".lower(),
                   #                   "0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23".lower(),
                   #                   "0xd9007A12b33b699Ee01B7D6f9D9fEae42AB5145C".lower(),
                   "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA".lower()
                   ]

MIN_DFLOP = 300


class GpuCatcher:

    def __init__(self, addr: str, vast: VastClient):
        self.addr = addr
        self.s1 = State(S_STARTED, [f"Frequency in minutes: {FREQUENCY_M}"], self.state_run)
#        self.s_buy_miners = State(S_DONE, self.state_completed)
        self.sm = StateMachine([self.s1])
        self.vast = vast
        self.automation = Automation(vast)
        self.previous_time_tick = datetime.now()


    def get_state_machine(self):
        return self.sm


    def state_run(self, time_tick: datetime) -> State:

        diff = time_tick.timestamp() - self.previous_time_tick.timestamp()
        print("Jaha: ", str(diff/60))

        if diff > 50+60:
            self.previous_time_tick = time_tick
            self.buy_cheap_a5000()

        return self.s1


    def buy_cheap_a5000(self):
        self.print_attention("Buy cheap miners...")

        offers: list[VastOffer] = self.automation.offers_A5000(MIN_DFLOP)
        self.buy_miners(offers)
        self.print_attention("Done!")


    def buy_miners(self, offers: list[VastOffer]) -> list[int]:
        bought_instances = []

        if len(offers) == 0:
            print(Field.attention(f"No offers above required flops per dph found: {MIN_DFLOP}"))
        else:
            for offer in offers:
                #                        best_offer: VastOffer = offers
                # Increase bid price
                price: float = offer.min_bid
                price = price * 1.02

                if offer.flops_per_dphtotal > MIN_DFLOP:
                    print(Field.attention(f"Creating instance: {offer.id}"))
                    created_id = self.vast.create_instance(self.addr, offer.id, price)
                    bought_instances.append(created_id)

        return bought_instances


    def print_attention(self, info: str):
        text = self.sm.next_state.name + ": " + info
        print(f.format(text))
