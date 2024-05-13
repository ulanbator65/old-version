# External modules
from dotenv import load_dotenv
import logging

# My modules
from db.DbManager import DbManager
#from VastClient import *
from VastAiCLI import VastAiCLI
from views.BuyMenu import BuyMenu
from views.MainMenu import MainMenu
from views.TerminateMenu import *
from statemachine.Controller import Controller
from XenblocksHistoryManager import XenblocksHistoryManager
from db.HistoryManager import HistoryManager
from AutoMiner import AutoMiner
import app_config as app
import config as config
from constants import *
from integrationtest import integration_tests


logging.basicConfig(level=logging.INFO)
load_dotenv()  


# ui.display_splash_screen()


def main():
#    app.set_db_manager(DbManager(config.DB_NAME))
#    app.set_vast_ai_command(VastAiCLI(config.API_KEY))
#    a = VastClient(config.API_KEY, config.BLACKLIST)
#    app.set_vast_client(a)

    # vast = VastClient(config.API_KEY, config.BLACKLIST)

    vast: VastClient = VastClient(config.API_KEY, config.BLACKLIST)

    buy = BuyMenu(vast)
    terminate = TerminateMenu(vast)
    main_menu = MainMenu(buy, terminate, vast)

    integration_tests.run_all_tests()

    print_config()

    if config.RUN_STATE_MACHINES:
        controller = Controller()

        #            xuni = XuniMinerV2(self.vast, 1).get_state_machine()
        #            gpu = GpuCatcher(config.ADDR, self.vast, 3).get_state_machine()
        #            offline = OfflineMinerManager(self.vast, 3).get_state_machine()
        #            controller.add_state_machine(xuni)

        history = XenblocksHistoryManager(vast, HistoryManager(), 2).get_state_machine()
        controller.add_state_machine(history)

        #            controller.add_state_machine(gpu)
        #            controller.add_state_machine(offline)

        auto = AutoMiner(vast, 1).get_state_machine()
        controller.add_state_machine(auto)

        controller.run()
    else:
        main_menu.start()


def print_config():
    COL = GOLD
    COL2 = LIGHT_PINK
    indent = " "*25
    # Print out the configuration settings
    print("")
    print(indent + f"  {COL}{'=' * 60}{RESET}")
    print(indent + f"  {COL}||{'VAST Monitor v2.0'.center(56)}||{RESET}")
    print(indent + f"       {LIGHT_CYAN2}User Configuration:{RESET}")
    print(indent + f"       Address: {COL2}{config.ADDR}{RESET}")
    print(indent + f"       Image: {COL2}{config.VAST_IMAGE}{RESET}")
    print(indent + f"       Database: {COL2}{config.DB_NAME}, {config.HISTORY_DB}{RESET}")
    print(indent + f"       Manual Mode: {COL2}{config.MANUAL_MODE}{RESET}")
    print(indent + f"  {COL}||{' '.center(56)}||{RESET}")
    print(indent + f"  {COL}{'=' * 60}{RESET}\n")


if __name__ == "__main__":
    main()
