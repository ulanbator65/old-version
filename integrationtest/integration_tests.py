
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
    cache: list = XenBlocksCache.get_all_balances()
    if len(cache) < 5:
        raise Exception("Expected cache size to be grater than: 5")
    for c in cache:
        print(c)


def test_db():
    DbTest().run_test()
