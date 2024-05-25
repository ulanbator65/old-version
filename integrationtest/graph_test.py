
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

    vast_balances: list[tuple] = VastBalanceHistoryRepo().get_from_timestamp(0)
    vast_balances.reverse()

    time_axis = []
    y1_axis = []
    y2_axis = []
    y3_axis = []
    t0 = None
    b0 = None
    c0 = None
    t1 = None
    b1 = None
    c1 = None

    balances = get_balances()
    timestamps = balances[0]
    blocks = balances[1]
    usd = balances[2]

    for idx, tt in enumerate(timestamps):

        if b0:
#            print("B1 ", b1)
            t1 = timestamps[idx]
            b1 = blocks[idx]
            c1 = usd[idx]

            delta_time = (t1 - t0) / 3600

            # Sample about once per hour or so
            if delta_time > 0.69:
                delta_block = (b1 - b0)
                delta_block = delta_block if delta_block > 0.0 else 0.1
                rate = delta_block / delta_time
                rate = rate if rate < 18 else 18
                cost = abs(c1 - c0) / delta_time
                block_cost = cost/delta_block

                # Normalize values so they become easier to compare in the graph
                # Also truncate any outliers
                block_cost = block_cost if block_cost < 0.12 else 0.12
                norm_cost = 10 * cost
                norm_cost = norm_cost if norm_cost < 16.0 else 16.0

                time_axis.append(datetime.fromtimestamp(t1))
                y1_axis.append(rate)
                y2_axis.append(norm_cost)
                y3_axis.append(100*block_cost)
                b0 = b1
                t0 = t1
                c0 = c1

        # Initialize first iteration
        else:
            b0 = blocks[idx]
            t0 = timestamps[idx]
            c0 = usd[idx]

    graph.print_graph("Block per hour", time_axis, y1_axis, y2_axis, y3_axis)


def get_balances() -> tuple:
    vast_balances: list[tuple] = VastBalanceHistoryRepo().get_from_timestamp(0)
    vast_balances.reverse()

    timestamps = []
    block_count = []
    usd_balance = []

    for b in vast_balances:
        t = b[0]
        usd = b[1]
        balances = HistoryManager().get_wallet_balances(t)
        total_block = get_total_block_balance(balances)

        timestamps.append(t)
        block_count.append(total_block)
        usd_balance.append(usd)

    return timestamps, block_count, usd_balance


def get_total_block_balance(balances: list[XenBlocksWallet]) -> int:
    block = 0
    for b in balances:
        block += b.block

    return block

