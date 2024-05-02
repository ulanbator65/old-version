
from Field import Field
import XenBlocksCache
from db.DbTest import DbTest
from constants import *

fgreen = Field(GREEN)


def run_all():
    test_xenblocks_cache()
    test_db()
    print(fgreen.format("Integration tests completed successfully!"))


def test_xenblocks_cache():
    addr = "0xfAA35F2283dfCf6165f21E1FE7A94a8e67198DeA"
    wallet = XenBlocksCache.get_wallet_balance(addr)
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
