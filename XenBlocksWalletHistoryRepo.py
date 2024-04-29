
from contextlib import closing
from sqlite3 import Connection

from XenBlocksWallet import XenBlocksWallet
from DbManager import DbManager
from config import DB_NAME
from Field import Field
from constants import *

CREATE_TABLE = "CREATE TABLE IF NOT EXISTS miner_history (id STRING, timestamp INTEGER, block INTEGER, xuni INTEGER, sup INTEGER, cost NUMBER)"
SELECT = "SELECT * FROM miner_history WHERE id = ? ORDER BY timestamp DESC;"
SELECT_FROM_TIMESTAMP = "SELECT * FROM miner_history WHERE id = ? and timestamp < ? ORDER BY timestamp DESC;"
INSERT = "INSERT INTO miner_history VALUES(?, ?, ?, ?, ?, ?)"
#UPDATE = "UPDATE miner_history SET timestamp=?, blocks=?, timestamp=? WHERE id=?"
DELETE = "DELETE FROM miner_history WHERE id=?"
DELETE_ALL = "DELETE FROM miner_history"

error = Field(RED)


class XenBlocksWalletHistoryRepo:
    def __init__(self, db_man: DbManager = DbManager(DB_NAME)):
        self.db: DbManager = db_man
        self.connection: Connection = None
#        print(json)
#        self.db = "database.db"
#        self.db = sqlite3.connect("database.db")

        with closing(self.__open()) as connection:
            self.__create_table()
            self.connection.commit()


    def get_nr_of_rows(self, addr: str):
        return len(self.get(addr))


    def create(self, snapshot: XenBlocksWallet):
        if snapshot.block < 200:
            # This seems to be a delta count and not the total counter
           raise Exception("WTF!!!")

        params: tuple = (snapshot.addr, snapshot.timestamp_s, snapshot.block, snapshot.sup, snapshot.xuni, snapshot.cost_per_hour)
        if snapshot.sup == 0 and snapshot.block > 1100:
            # A bug in XenBlocks endpoint where super count is sometimes returned as zero
            # Ignore faulty data
            print(error.format("Super count with '0' detected. Will not save to database!!!"))
            print(str(params))
#            raise Exception("WTF2!!!")
        else:
            self.db.insert(INSERT, params)

#        with closing(self.__open()) as connection:
#            self.__insert(id, timestamp, stats.block, stats.super, stats.xuni, stats.cost_per_hour)
#            self.connection.commit()


    def get_for_timestamp(self, addr: str, timestamp: int) -> XenBlocksWallet:
        params: tuple = (addr, timestamp)
        result = self.db.select(SELECT_FROM_TIMESTAMP, params)

        return self.map_row(result[0]) if len(result) > 0 else None


    def get_latest_version(self, id: str) -> XenBlocksWallet:
        params: tuple = (id,)
        result = self.db.select(SELECT, params)
        return self.map_row(result[0]) if len(result) > 0 else None


    def get(self, addr: str, max_count: int = 99) -> list[tuple]:
        params: tuple = (addr,)
        result = self.db.select(SELECT, params)
        return result[0:max_count] if len(result) >= max_count else result

#        with closing(self.__open()) as connection:
#            result = connection.cursor().execute(SELECT, (id,)).fetchall()
#            return result[0:max_count] if len(result) >= max_count else result


    def map_row(self, row: tuple) -> XenBlocksWallet:
        addr: str = row[0]
        timestamp_s: int = row[1]
        block: int = row[2]
        sup: int = row[3]
        xuni: int = row[4]
        cost: float = row[5]
        return XenBlocksWallet(addr, 0, block, sup, xuni, timestamp_s, cost)


    def __create_table(self):
        self.execute(CREATE_TABLE)

    def __delete(self, id: str):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(DELETE, id)

    def delete_all(self):
        with closing(self.__open()) as connection:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(DELETE_ALL)
            self.connection.commit()

    def execute(self, sql: str):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql)
        self.connection.commit()

    def __open(self):
        self.connection = self.db.open()
        return self.connection

