
from datetime import datetime, timedelta
import graphs.graph as graph
from db.HistoryManager import HistoryManager
from db.VastBalanceHistoryRepo import VastBalanceHistoryRepo
from db.XenBlocksWalletHistoryRepo import XenBlocksWalletHistoryRepo
from XenBlocksWallet import XenBlocksWallet
import config


def test_all2():

    addr = "0xe977d33d9d6d9933a04f1beb102aa7196c5d6c23"
    t1 = datetime.now()
    t0 = t1 - timedelta(hours=24)
    t_fallback = t1 - timedelta(hours=1)

    balances: list[XenBlocksWallet] = XenBlocksWalletHistoryRepo().get_history(addr)
    balances.reverse()
    print(len(balances))

    time_axis = []
    y_axis = []
    b0 = None
    b1 = None

    for b in balances:
        b1 = b

        if b0:
            delta_time = (b1.timestamp_s - b0.timestamp_s) / 3600
            delta_block = (b1.block - b0.block)

            # Sample about once per hour or so
            if delta_time > 1.95:
                rate = delta_block / delta_time

                time_axis.append(datetime.fromtimestamp(b1.timestamp_s))
                y_axis.append(rate)
                b0 = b1
        else:
            b0 = b1

#    print(balances_y)
    graph.print_graph("Block per hour", time_axis, y_axis)


def test_all1():
    pass


def test_all():

#    t1 = datetime.now()
#    t0 = t1 - timedelta(hours=24)
#    t_fallback = t1 - timedelta(hours=1)

    vast_balances: list[tuple] = VastBalanceHistoryRepo().get_from_timestamp(0)
    vast_balances.reverse()

    time_axis = []
    y_axis = []
    t0 = None
    b0 = None
    t1 = None
    b1 = None

    balances = get_balances()
    timestamps = balances[0]
    blocks = balances[1]

    for idx, tt in enumerate(timestamps):

        if b0:
#            print("B1 ", b1)
            t1 = timestamps[idx]
            b1 = blocks[idx]

            delta_time = (t1 - t0) / 3600

            # Sample about once per hour or so
            if delta_time > 1.2:
                delta_block = (b1 - b0)
                rate = delta_block / delta_time

                time_axis.append(datetime.fromtimestamp(t1))
                y_axis.append(rate)
                b0 = b1
                t0 = t1

        # Initialize first iteration
        else:
            b0 = blocks[idx]
            t0 = timestamps[idx]

    graph.print_graph("Block per hour", time_axis, y_axis)


def get_balances() -> tuple:
    vast_balances: list[tuple] = VastBalanceHistoryRepo().get_from_timestamp(0)
    vast_balances.reverse()

    timestamps = []
    block_count = []

    for b in vast_balances:
        t = b[0]
        balances = HistoryManager().get_wallet_balances(t)
        total_block = get_total_block_balance(balances)

        timestamps.append(t)
        block_count.append(total_block)

    return timestamps, block_count


def get_total_block_balance(balances: list[XenBlocksWallet]) -> int:
    block = 0
    for b in balances:
        block += b.block

    return block


def delta(p0: tuple, p1: tuple) -> tuple:

    delta_time = (p1[0] - p0[0]) / 3600
    delta_block = (p1[1] - p0[1])

    return p1[0], delta_block

