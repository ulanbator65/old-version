
from sqlite3 import Connection

from XenBlocksWallet import XenBlocksWallet
from db.DbManager import DbManager
from config import DB_NAME
from Field import Field
from constants import *

CREATE_TABLE = "CREATE TABLE IF NOT EXISTS miner_history (id STRING, timestamp INTEGER, block INTEGER, xuni INTEGER, sup INTEGER, cost NUMBER)"
SELECT = "SELECT * FROM miner_history WHERE id = ? ORDER BY timestamp DESC;"
SELECT_FROM_TIMESTAMP = "SELECT * FROM miner_history WHERE id = ? and timestamp > ? ORDER BY timestamp DESC;"
INSERT = "INSERT INTO miner_history VALUES(?, ?, ?, ?, ?, ?)"
DELETE = "DELETE FROM miner_history WHERE id=?"
DELETE_ALL = "DELETE FROM miner_history"

error = Field(RED)

#"ALTER TABLE miner_history ADD new_column_name column_definition;"


class XenBlocksWalletHistoryRepo:
    def __init__(self, db_man: DbManager = DbManager(DB_NAME)):
        self.db: DbManager = db_man
        self.connection: Connection = None

        self.db.execute(CREATE_TABLE)


    def get_nr_of_rows(self, addr: str):
        return len(self.get(addr))


    def create(self, snapshot: XenBlocksWallet) -> bool:
        if snapshot.block < 200:
            # This seems to be a delta count and not the total counter
           raise Exception("WTF!!!")

        params: tuple = (snapshot.addr, snapshot.timestamp_s, snapshot.block, snapshot.sup, snapshot.xuni, snapshot.cost_per_hour)

        if snapshot.sup == 0 and snapshot.block > 1600:
            # A bug in XenBlocks endpoint where super count is sometimes returned as zero
            # Ignore faulty data
#            print(error.format("Super count with '0' detected. Will not save to database!!!"))
#            print(str(params))
            previous = self.get_latest_version(snapshot.addr)

            params = (snapshot.addr, snapshot.timestamp_s, snapshot.block, previous.sup, snapshot.xuni, snapshot.cost_per_hour)

        return self.db.insert(INSERT, params)


    def get_for_timestamp(self, addr: str, timestamp: int) -> XenBlocksWallet:
        result = self.get_history(addr, timestamp)

        return result[0] if len(result) > 0 else None


    def get_history(self, addr: str, timestamp: int) -> list[XenBlocksWallet]:
        params: tuple = (addr, timestamp)
        result = self.db.select(SELECT_FROM_TIMESTAMP, params)

        history: list[XenBlocksWallet] = []

        for x in result:
            history.append(self.map_row(x))

        return history


    def get_latest_version(self, id: str) -> XenBlocksWallet:
        params: tuple = (id,)
        result = self.db.select(SELECT, params)
        return self.map_row(result[0]) if len(result) > 0 else None


    def get(self, addr: str, max_count: int = 99) -> list[tuple]:
        params: tuple = (addr,)
        result = self.db.select(SELECT, params)
        return result[0:max_count] if len(result) >= max_count else result


    def map_row(self, row: tuple) -> XenBlocksWallet:
        addr: str = row[0]
        timestamp_s: int = row[1]
        block: int = row[2]
        sup: int = row[3]
        xuni: int = row[4]
        cost: float = row[5]
        return XenBlocksWallet(addr, 0, block, sup, xuni, timestamp_s, cost)


    def __delete(self, id: str):
        self.db.delete(DELETE, (id,))

    def delete_all(self):
        self.db.execute(DELETE_ALL)

