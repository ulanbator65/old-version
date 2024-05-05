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

    buy = BuyMenu()
    terminate = TerminateMenu()
    main_menu = MainMenu(buy, terminate)

    integration_tests.run_all_tests()

    print_config()

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
    print(indent + f"       Database: {COL2}{config.DB_NAME}{RESET}")
    print(indent + f"       Manual Mode: {COL2}{config.MANUAL_MODE}{RESET}")
    print(indent + f"  {COL}||{' '.center(56)}||{RESET}")
    print(indent + f"  {COL}{'=' * 60}{RESET}\n")


if __name__ == "__main__":
    main()
