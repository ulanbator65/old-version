
from datetime import datetime, timedelta
from db.VastBalanceHistoryRepo import VastBalanceHistoryRepo
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from db.HistoryManager import HistoryManager
from XenBlocksWallet import XenBlocksWallet
from constants import *


def all_tests():
    test_integrity()
    test_history_manager()
    test_vast_balance_history()


def test_vast_balance_history():
    count = XenBlocksWalletHistoryRepo().count()
    print(count)

    if count < 1:
        raise Exception("WTF!!!")

    delta_hours1 = 0.4
    fallback = 1.7

    t0 = datetime.now()
    t1 = t0 - timedelta(minutes=delta_hours1*60)
    fallback_time = t0 - timedelta(minutes=fallback*60)

    balances = HistoryManager().get_balances_with_fallback(int(t1.timestamp()), int(fallback_time.timestamp()))
    print("T0: ", str(int(t0.timestamp())))
    print("T1: ", str(int(t1.timestamp())))
    print("Fallback: ", str(int(fallback_time.timestamp())))

    print("Found Timestamp: ", str(balances.timestamp))


    vast_balance = balances.vast_balance

    print("First >>>> " + str(vast_balance))

    balance = VastBalanceHistoryRepo().get(int(balances.timestamp))
    if balance < 0.001:
        raise Exception("No VAST balance found!!")


def test_integrity():
    history = HistoryManager()
    history.cleanup_db()


    wallet_db = XenBlocksWalletHistoryRepo()

    timestamp = int(datetime.now().timestamp())
    timestamp = 112233

    wallet = XenBlocksWallet("Kalle", 999999, 1123, 2, 555, timestamp, 0)
    wallet_db.create(wallet)

    created_wallet = wallet_db.get_for_timestamp(timestamp)

    if not created_wallet or len(created_wallet) == 0:
        raise Exception("WWTTFF!!!")

    wallet_db.delete(timestamp)


    all_balances = VastBalanceHistoryRepo().get_all()
    print("VAST balances: ", len(all_balances))

    if len(all_balances) < 1:
        raise Exception("Balances table is empty!!!")

    count = XenBlocksWalletHistoryRepo().count()
    print("Wallets history: ", count)

    for b in all_balances:
        result = XenBlocksWalletHistoryRepo().get_for_timestamp(b[0])
        if not result:
            raise Exception("WTF!")




def test_history_manager():
    now = int(datetime.now().timestamp())

    #    all_balances = VastBalanceHistoryRepo().get_from_timestamp(timestamp + 20*60)


    historic_time = datetime.fromtimestamp(now) - timedelta(minutes=5*60)
    historic_balances = HistoryManager().get_balances(int(historic_time.timestamp()))

    print(GREEN + "Diff: ", (now - historic_balances.timestamp)/3600, RESET)
    print(GREEN + "Time: ", datetime.fromtimestamp(historic_balances.timestamp), RESET)
    for b in historic_balances.wallet_balances:
        print(b.to_str())


def to_string(balance: tuple) -> str:
    t = datetime.fromtimestamp(balance[0])

    return f"Bal:  {t} {balance[1]:0.1f}"
