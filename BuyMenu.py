
from VastClient import VastClient
from VastOffer import VastOffer
from Automation import *
from prettytable.colortable import *
from constants import *
from Menu import *
from ui import text_color


class BuyMenu:
    def __init__(self, vast: VastClient = VastClient(config.API_KEY, config.BLACKLIST)):
        self.vast = vast
        self.auto = Automation(vast)


    def auto_buy(self):
        self.auto.runBot()


    def buy_instance_menu(self):
        running = True
        menu = self.get_menu()

        while running:
            offer_type = menu.select()

            if offer_type.upper() == CH_EXIT:
                break

            # Auto
            elif offer_type == '0':
                offer_selection = self.auto.offers_A40()
                if len(offer_selection) > 0:
                    self.print_offer_table(offer_selection)

            # RTX 3060/3090
            elif offer_type == '7':
                offer_selection = self.auto.offers_30_series()
                if len(offer_selection) > 0:
                    self.print_offer_table(offer_selection)

            # A40
            elif offer_type == '8':
                offer_selection = self.auto.offers_A40(199)
                if len(offer_selection) > 0:
                    self.print_offer_table(offer_selection)
                    self.__select_and_purchase(offer_selection)
                    return

            # Preview result
            elif offer_type == 'T':
                offer_selection = self.auto.selectTopOffers()
                if len(offer_selection) > 0:
                    print("First item: ", offer_selection[0])
                    self.print_offer_table(offer_selection)
                    offer_selection = []

            # Other
            else:
                criterion: dict = {'1': 'dph_total', '2': 'total_flops', '3': 'flops_per_dphtotal'}.get(offer_type, '')
                gpu_model: dict = {
                    '4': 'RTX_A2000',
                    '5': 'RTX_A4000',
                    '6': 'RTX_A5000',
                    '7': 'RTX_3060',
                    '8': 'A40',
#                    '8': 'RTX_3060_Ti',
                    '9': 'RTX_3070'
                }.get(offer_type, '')

                self.select_top_offers(criterion=criterion, gpu_model=gpu_model, max_bid=0.7)


    def select_top_offers(self, criterion: dict, gpu_model: dict, max_bid=0.7):

        top_offers = self.search_top_offers(50, max_bid, criterion=criterion, gpu_model=gpu_model)

        self.print_offer_table(top_offers)
        self.__select_and_purchase(top_offers)


    def __select_and_purchase(self, offers: list):
#        self.print_offer_table(offers)

        selection = input("\nEnter the numbers of the offers to purchase, or 'x' to exit: ").upper()

        if selection == CH_EXIT:
            return

        selected_indices = self.parse_selection(selection)
        print("Selection: ", selected_indices)

        for idx in selected_indices:
            self.purchase_offer(offers[idx-1])


    def purchase_offer(self, offer: VastOffer):
        confirm = ui.get_choice("\nConfirm purchase? (y/n): ").lower()

        if confirm.startswith('y'):
            result = self.create_instance(offer)
            self.print_result(result, offer.id)
        else:
            print("Operation cancelled!")


    def create_instance(self, offer: VastOffer) -> dict:
        print("Price: ", offer.dph_total)
        price = offer.increase_price(1)
        print("Adjusted Price: ", price)

        return self.vast.create_instance(config.ADDR, offer.id, price)


    def print_result(self, result: dict, id: int):
        table: ColorTable = ColorTable(theme=THEME2)
        table.field_names = ["Offer ID", "Response from Vast.ai", "State"]

        if result:
            print("Result: ", result)
            response_from_vast = "Started"
            state = "Success: True" if result.get('success') else "Success: False"
            row = [text_color(str(id)), text_color(response_from_vast), text_color(state)]
            table.add_row(row)
        else:
            table.add_row([
                f"\033[92m{id}",
                "\033[92mFailed to receive proper response",
                "\033[92mN/A"
            ])

        print(table)


    def purchase(self, selected_indices: list, top_offers: list):
        for index in selected_indices:

            if 1 <= index <= len(top_offers):
                selected_offer = top_offers[index - 1]
                print(f"Purchasing offer ID {selected_offer.id}")
                self.vast.create_instance1(selected_offer)
#                self.vast.create_instance(selected_offer['id'], selected_offer['dph_total'])
            else:
                print(f"Invalid selection: {index}. Please try again.")


    def search_top_offers(self, max_result: int, max_bid: float,
                          criterion='dph_total', gpu_model='') -> list[VastOffer]:

        query = VastQuery.gpu_model_query(gpu_model)
        query.max_bid = max_bid
        query.verified = False

        offers_response = self.vast.get_offers(query)

        if isinstance(offers_response, list):
            offers = offers_response
            #        column = 'dph_total'
            sorted_offers = sorted(offers, key=lambda x: x.flops_per_dphtotal, reverse=True)
            return sorted_offers[:max_result]
        else:
            print("Unexpected response format. Please ensure your command execution function is correct.")
            return []


    def parse_selection(self, input_str):
        """
        Parses a string input like '1-3,5' into a list of numbers [1, 2, 3, 5].
        """
        selection = set()
        for part in input_str.split(","):
            if '-' in part:
                start, end = map(int, part.split('-'))
                selection.update(range(start, end + 1))
            else:
                selection.add(int(part))

        return sorted(selection)


    @staticmethod
    def print_offer_table(offers: list):
        if not offers:
            print("No offers to display.")
            return

        table: ColorTable = ColorTable(theme=THEME2)
        table.field_names = ["Number", "ID", "GPU", "Quantity", "Price/hr", "Total TFLOPS", "TFLOPS/$", "Location"]
        table.align = "l"

        for idx, offer in enumerate(offers, start=1):
            f = Field(BuyMenu.dflops_color(offer.flops_per_dphtotal))
            number = f.format(str(idx))
            offer_id = f.format(str(offer.id))
            gpu = f.format(offer.get('gpu_name').replace('_', ' '))
            quantity = f.format(str(offer.get('num_gpus', 'N/A')))
            price_hr = f.format(f"${offer.get('dph_total'):.3f}")
            total_tflops = f.format(f"{offer.get('total_flops'):.2f}")
            tflops_per_dph = f.format(str(offer.flops_per_dphtotal))
            location = f.string(offer.get('geolocation', 'Unknown'))

            table.add_row([number, offer_id, gpu, quantity, price_hr, total_tflops, tflops_per_dph, location])

        print(table)


    def get_menu(self) -> Menu:
        menu_items: list = \
            ["   0. Auto",
                "   1. Lowest Price/hr",
                "   2. Highest Total TFLOPS",
                "   3. Highest TFLOPS/$",
                "   4. RTX A2000 Offers",
                "   5. RTX A4000 Offers",
                "   6. RTX A5000 Offers",
                "   7. RTX 3060,3090 Offers",
                "   8. A40 Offers",
                "   9. RTX 3070 Offers",
                "   X. Exit to previous menu"]

        return Menu("Search for the top offers", menu_items, 50, LIGHT_PINK, LIGHT_YELLOW)


    @staticmethod
    def dflops_color(dflops) -> str:
        top_rate = 300
        mid_rate = 200
        if dflops <= mid_rate:
            return GRAY
        elif dflops < top_rate:
            return C_WARNING
        elif dflops >= top_rate:
            return C_OK
        else:
            return C_ERROR
