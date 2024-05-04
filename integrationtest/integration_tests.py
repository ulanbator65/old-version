
from Field import Field
import XenBlocksCache
from db.DbTest import DbTest
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from constants import *
from datetime import datetime
from statemachine.State import State
from statemachine.StateMachine import StateMachine

fgreen = Field(GREEN)


def run_all_tests():
    print(fgreen.format("Integration tests started..."))
    test_state_machine()
    test_vast_deserialization()
    test_xenblocks_wallet_history()
#    test_xenblocks_cache()
    test_db()
    print(fgreen.format("Integration tests completed successfully!"))


def state1(time_tick):
    print("State1: ", time_tick)
    return State("S2", [], state2)


def state2(time_tick):
    print("State2: ", time_tick)
    return State("S1", [], state1)


def test_state_machine():
    s1: State = State("S1", [], state1)
    s2: State = State("S2", [], state2)

    sm = StateMachine([s1, s2])
    sm.execute(datetime.now())
    if sm.next_state.name != "S2":
        raise Exception("Expected state S2!")

    sm.execute(datetime.now())
    if sm.next_state.name != "S1":
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


def test_xenblocks_wallet_history():
    addr = "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA"
    history = XenBlocksWalletHistoryRepo().get(addr.lower())

    if len(history) < 1:
        raise Exception("No history found!")

    max = len(history) - 1 if len(history) < 10 else 9
    history = history[0:max]

    for h in history:
        print(to_str(h))


def test_db():
    DbTest().run_test()


def to_str(wallet: tuple):
    time = datetime.fromtimestamp(wallet[1])
    return f"addr: {wallet[0]}, time: {time}, block: {wallet[2]}, super: {wallet[3]}"
