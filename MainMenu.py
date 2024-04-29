
import ui
from VastClient import VastClient
from InstanceTable import InstanceTable
from TerminateMenu import TerminateMenu
from Automation import *
from AutoMiner import AutoMiner
from BuyMenu import BuyMenu
from MinerStatisticsTable import MinerStatisticsTable
from MinerGroup import MinerGroup
from Menu import *
from MinerStatisticsTable import MinerStatisticsTable
from XuniMiner import XuniMiner
from MinerCatcher import MinerCatcher
from DbTest import DbTest
import config


AUTO = '0'
VIEW_INSTANCE = '1'
KILL_INSTANCES = '2'
BUY_INSTANCE = '3'
REBOOT = '4'
REFRESH_MINER_STATS = '5'
INCREASE_BID = '6'
M_RESET = '7'
M_EXIT = 'x'
PURGE_INSTANCES = '44'


class MainMenu:

    def __init__(self, buy, terminate: TerminateMenu, vast: VastClient = VastClient(config.API_KEY, config.BLACKLIST)):
        self.vast = vast
        self.buy: BuyMenu = buy
        self.terminate = terminate
        self.automation = Automation(vast)
        self.table = InstanceTable()
        self.miner_stat_table = MinerStatisticsTable(self.vast)
    #    print(vast)


    def start(self):
#        self.buy.auto_buy()
        self.main_menu_selection(VIEW_INSTANCE)
        #        self.buy.buy_instance_menu()
        running = True
        main_menu: Menu = self.get_menu()

        DbTest().run_test()

        if config.SHOW_MINER_GROUPS:
            self.miner_stat_table.print()

        if config.RUN_XUNI_MINER:
            XuniMiner(self.vast).mine_xuni()

        while running:
            choice = main_menu.select()
            running = self.main_menu_selection(choice)


    def get_menu(self) -> Menu:
        menu_items = []
        menu_items.append("   0. Automation")
        menu_items.append("   1. View Running Instances")
        menu_items.append("   2. Kill Instances")
        menu_items.append("   3. Buy an Instance")
        menu_items.append("   4. Reboot")
        menu_items.append("   5. Refresh miner statistics (Enter)")
        menu_items.append("   6. Increase bid")
        menu_items.append("   7. Reset hours")
        menu_items.append("   ")
        menu_items.append("   9. Reboot")
        menu_items.append("   Exit (x)")
        return Menu("Main Menu", menu_items, 50)


    def main_menu_selection(self, choice):

        if choice == AUTO:
            self.automation.runBot()
            # result = ShellCommand().run("ssh -p 19267 root@210.239.9.203 -L 8080:localhost:8080")
#           result = ShellCommand().run(["ssh", "-p", "19267", "root@210.239.9.203", "-L", "8080:localhost:8080"])
#            print(result)

        elif choice == VIEW_INSTANCE:
            self.table.refresh()
            self.table.print_table()

        elif choice == REFRESH_MINER_STATS:
            self.table.load_miner_stats()
            self.table.print_table()

        elif choice == BUY_INSTANCE:
            self.buy.buy_instance_menu()

        elif choice == KILL_INSTANCES:
            self.terminate.instance_termination_menu(self.table)
            self.main_menu_selection(VIEW_INSTANCE)

        elif choice == REBOOT:
            self.reboot_instances()

        elif choice == PURGE_INSTANCES:
            self.terminate.purge_dead_instances(self.table)

        elif choice == INCREASE_BID:
            pass
#            self.automation.increase_bid(self.table.instances)

        elif choice == M_RESET:
            self.table.reset_hours()
            self.main_menu_selection(VIEW_INSTANCE)

        elif choice == M_EXIT or choice == CH_EXIT:
            print("Exiting...")
            return False

        else:
            self.main_menu_selection(REFRESH_MINER_STATS)
            print("Invalid option, please try again.")

        return True


    def auto_menu(self):
        choice = self.get_auto_menu().select()
        self.auto_menu_selection(choice)


    def auto_menu_selection(self, choice):

        if choice == '1':
            AutoMiner(self.vast).start_mining()

        if choice == '2':
            MinerCatcher(self.vast).catch_miners()


    def reboot_instances(self):
        VastInstanceRules.is_outbid()
        self.vast.reboot_instance()


    def get_auto_menu(self) -> Menu:
        menu_items = []
        menu_items.append("   1. Auto Miner")
        menu_items.append("   2. Catch cheap miners")
        menu_items.append("   Exit (x)")
        return Menu("Main Menu", menu_items, 50)


