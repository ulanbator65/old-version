
from datetime import datetime
from views.BuyMenu import BuyMenu
from Menu import *
from MinerHistoryTable import MinerHistoryTable
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from XenblocksHistoryManager import XenblocksHistoryManager
from InstanceTable import InstanceTable

import config
import constants
import time
import logger as log
import XenBlocksCache


VIEW_INSTANCE = '1'
KILL_INSTANCES = '2'
BUY_INSTANCE = '3'
REBOOT = '4'
INCREASE_BID = '6'
M_EXIT = 'x'
PURGE_INSTANCES = '44'


DFLOP_MIN = 500


class OfflineMenu:

    def __init__(self, buy: BuyMenu, vast: VastClient = VastClient(config.API_KEY, config.BLACKLIST)):
        self.vast = vast
        self.buy: BuyMenu = buy
        self.automation = Automation(vast)
        self.table = InstanceTable()


    def run(self):
        running = True
        main_menu: Menu = self.get_menu()

        while running:
            choice = main_menu.select()
            running = self.menu_selection(choice)


    def get_menu(self) -> Menu:
        items = []
        items.append("   1. View Running Instances")
        items.append("   2. ")
        items.append("   3. ")
        items.append("   4. Reboot")
        items.append("   5. ")
        items.append("   6. Increase bid")
        items.append("   Exit (x)")
        return Menu("Manage Offline Miners", items, 50)


    def menu_selection(self, choice):

        self.table.refresh()

        if choice == VIEW_INSTANCE:
            self.table.print_table()

        elif choice == REBOOT:
            self.reboot_instances()

        elif choice == INCREASE_BID:
#            pass
            self.automation.increase_bid(self.table.instances, DFLOP_MIN)

        elif choice == M_EXIT or choice == CH_EXIT:
            print("Exiting...")
            return False

        else:
            print("Invalid option, please try again.")

        return True


    def reboot_instances(self):
        self.table.refresh()

        for inst in self.table.instances:
            if inst.is_running():
                self.vast.reboot_instance(inst.id)


