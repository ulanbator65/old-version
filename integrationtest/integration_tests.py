
from Field import Field
from VastClient import VastClient
import XenBlocksCache
from db.DbTest import DbTest
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from db.HistoryManager import HistoryManager
from db.VastBalanceHistoryRepo import VastBalanceHistoryRepo
from OfflineMinerManager import OfflineMinerManager
from constants import *
from datetime import datetime, timedelta
from statemachine.State import State
from statemachine.StateMachine import StateMachine
import integrationtest.history_manager_test as history
import integrationtest.graph_test as graph_test

fgreen = Field(GREEN)


def run_all_tests():
    print(fgreen.format("Integration tests started..."))

    test_vast_deserialization()
    test_db()

    history.test_integrity()
    history.test_vast_balance_history()

    graph_test.test_all()

    print(fgreen.format("Integration tests completed successfully!"))


def run_tests_part2():
#    OfflineMinerManager(VastClient()).test()
    test_state_machine()
    test_xenblocks_cache()


def state1(time_tick):
    print("State1: ", time_tick)
    return State("S2", [], state2)


def state2(time_tick):
    print("State2: ", time_tick)
    return State("S1", [], state1)


def test_state_machine():
    s1: State = State("S1", [], state1)
    s2: State = State("S2", [], state2)

    sm = StateMachine("Test State Machine", [s1, s2])
    sm.execute(datetime.now())
    if sm.state.name != "S2":
        raise Exception("Expected state S2!")

    sm.execute(datetime.now())
    if sm.state.name != "S1":
        raise Exception("Expected state S1!")


def test_vast_deserialization():
    stdout = "Started. {'success': False, 'new_contract': 10754064}"
    result = stdout.split("{")
    result = result[1].split("}")
    items = result[0].split(",")

    item2 = items[1].replace("'", "")
    item2 = item2.split(":")

    d: dict = {}
    d[item2[0].strip()] = item2[1].strip()

    if not int(d.get('new_contract')) == 10754064:
        raise Exception("Deserialization failed!")


def test_xenblocks_cache():
    addr = "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA"
    wallet = XenBlocksCache.get_wallet_balance(addr, int(datetime.now().timestamp()))

    if not wallet:
        raise Exception("Wallet not found!")

    if wallet.block < 1100:
        raise Exception("Wrong Wallet balance!")

    if wallet.addr != addr.lower():
        raise Exception("Wrong Wallet address!")

    wallet = XenBlocksCache.get_balance_for_rank(200)
    if wallet.rank != 200:
        raise Exception("Wrong rank: " + str(wallet.rank))



def test_db():
    DbTest().run_test()


def to_str(wallet: tuple):
    time = datetime.fromtimestamp(wallet[1])
    return f"addr: {wallet[0]}, time: {time}, block: {wallet[2]}, super: {wallet[3]}"
