
from datetime import datetime
from views.BuyMenu import BuyMenu
from views.TerminateMenu import TerminateMenu
from views.OfflineMenu import OfflineMenu
from Menu import *
from MinerPerformanceTable import MinerPerformanceTable
from VastCache import VastCache
from VastTradingBotSM import VastTradingBotSM
from HistoryManagerSM import HistoryManagerSM
from statemachine.Controller import Controller
from InstanceTable import InstanceTable

import config
import constants
import time
import logger as log
import XenBlocksCache


AUTO = '0'
VIEW_INSTANCE = '1'
KILL_INSTANCES = '2'
BUY_INSTANCE = '3'
MANAGE_OFFLINE = '4'
REFRESH_MINER_STATS = '5'
INCREASE_BID = '6'
M_RESET = '7'
HISTORIC_DATA = '8'
XUNI_MINER = '9'
M_EXIT = 'x'
PURGE_INSTANCES = '44'


class MainMenu:

    def __init__(self, buy, terminate: TerminateMenu, vast: VastClient = VastClient(config.API_KEY, config.BLACKLIST)):
        self.vast = vast
        self.buy: BuyMenu = buy
        self.terminate = terminate
        self.automation = Automation(vast)
        self.table = InstanceTable()
        self.miner_group_table = MinerPerformanceTable(VastCache(vast))


    def start(self):
#        self.main_menu_selection(VIEW_INSTANCE)

        running = True
        main_menu: Menu = self.get_menu()

        addr = ["0xe977d33d9d6D9933a04F1bEB102aa7196C5D6c23",
                "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA",
                "0x7c8d21F88291B70c1A05AE1F0Bc6B53E52c4f28a"]

        timestamp = int(datetime.now().timestamp())
        rank: XenBlocksWallet = XenBlocksCache.get_balance_for_rank(120, timestamp)
        w1_xuni: XenBlocksWallet = XenBlocksCache.get_wallet_balance(addr[0], timestamp)
        w2_xuni: XenBlocksWallet = XenBlocksCache.get_wallet_balance(addr[1], timestamp)
        w3_xuni: XenBlocksWallet = XenBlocksCache.get_wallet_balance(addr[2], timestamp)

        if rank:
            log.info(LIGHT_PINK + "Rank 120: " + rank.to_str())
            log.info(LIGHT_PINK + "XUNI: " + w1_xuni.to_str())
            log.info(LIGHT_PINK + "XUNI: " + w2_xuni.to_str())
            log.info(LIGHT_PINK + "XUNI: " + w3_xuni.to_str())


#        db = XenBlocksWalletHistoryRepo()
#        for a in addr:
#            snapshot = Cache.get_wallet_balance(a, int(datetime.now().timestamp()))
#            if snapshot:
#                log.info("Saving snapshot: " + snapshot.addr)
#                result = db.create(snapshot)


        if config.SHOW_MINER_GROUPS:
            self.miner_group_table.print()

        while running:
            choice = main_menu.select()
            running = self.main_menu_selection(choice)


    def get_menu(self) -> Menu:
        items = [" ",
                 "   0. Automation",
                 "   1. View Running Instances",
                 "   2. Kill Instances",
                 "   3. Buy an Instance",
                 "   ",
                 "   4. Manage Offline Miners",
                 "   5. Refresh miner statistics (Enter)",
                 "   6. Increase bid",
                 "   7. Reset hours",
                 "   ",
                 "   8. Historic data",
                 "   9. XUNI Miner",
                 "   Exit (x)"]
        return Menu("Main Menu", items, 50)


    def main_menu_selection(self, choice):

        if choice == AUTO:
            self.auto_menu()
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

        elif choice == MANAGE_OFFLINE:
            OfflineMenu(self.buy, self.vast).run()

        elif choice == PURGE_INSTANCES:
            self.terminate.purge_dead_instances(self.table)

        elif choice == INCREASE_BID:
#            pass
            self.automation.increase_bid(self.table.instances, 900)

        elif choice == M_RESET:
            self.table.reset_hours()
            self.main_menu_selection(VIEW_INSTANCE)

        elif choice == HISTORIC_DATA:
            self.miner_group_table.print()

        elif choice == XUNI_MINER:
            pass
#            XuniMiner(self.vast).mine_xuni()

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
            VastTradingBotSM(self.vast).start_mining()

        if choice == '2':
            pass
#            MinerCatcher(self.vast).catch_miners()


    def reboot_instances(self):
        self.table.refresh()

        for inst in self.table.instances:
            if inst.is_running():
                self.vast.reboot_instance(inst.cid)


    def shutdown_next_block(self):
        blocks = self.table.tot_block

        while True:
            time.sleep(60)

            self.table.refresh()

            if self.table.tot_block > blocks:
                for inst in self.table.instances:
                    if inst.is_running():
                        self.vast.kill_instance(inst.cid)

            break


    def get_auto_menu(self) -> Menu:
        menu_items = []
        menu_items.append("   1. Auto Miner")
        menu_items.append("   2. Catch cheap miners")
        menu_items.append("   Exit (x)")
        return Menu("Main Menu", menu_items, 50)


