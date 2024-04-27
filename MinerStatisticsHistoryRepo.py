
from contextlib import closing
from sqlite3 import Connection

from MinerStatistics import MinerStatistics
from DbManager import DbManager
from config import DB_NAME

CREATE_TABLE = "CREATE TABLE IF NOT EXISTS miner_history (id STRING, timestamp INTEGER, block INTEGER, xuni INTEGER, sup INTEGER, cost NUMBER)"
SELECT = "SELECT * FROM miner_history WHERE id=? ORDER BY timestamp DESC;"
SELECT_WITH_TIMESTAMP = "SELECT * FROM miner_history WHERE id=? and timestamp=? ORDER BY timestamp DESC;"
INSERT = "INSERT INTO miner_history VALUES(?, ?, ?, ?, ?, ?)"
#UPDATE = "UPDATE miner_history SET timestamp=?, blocks=?, timestamp=? WHERE id=?"
DELETE = "DELETE FROM miner_history WHERE id=?"
DELETE_ALL = "DELETE FROM miner_history"


class MinerStatisticsHistoryRepo:
    def __init__(self, db_man: DbManager = DbManager(DB_NAME)):
        self.db: DbManager = db_man
        self.connection: Connection = None
#        print(json)
#        self.db = "database.db"
#        self.db = sqlite3.connect("database.db")

        with closing(self.__open()) as connection:
            self.__create_table()
            self.connection.commit()


    def create(self, id: str, stats: MinerStatistics):
        if stats.block < 200:
            pass
            # This seems to be a delta count and not the total counter
 #           raise Exception("WTF!!!")

        params: tuple = (id, stats.timestamp_s, stats.block, stats.super, stats.xuni, stats.cost_per_hour)

        self.db.insert(INSERT, params)
#        with closing(self.__open()) as connection:
#            self.__insert(id, timestamp, stats.block, stats.super, stats.xuni, stats.cost_per_hour)
#            self.connection.commit()


    def get_for_timestamp(self, id: str, timestamp: int) -> MinerStatistics:
        params: tuple = (id, timestamp)
        result = self.db.select(SELECT_WITH_TIMESTAMP, params)
        if len(result) > 1:
            raise Exception("Two rows with same timestamp: " + id + str(timestamp))

        return self.map_row(result[0]) if len(result) > 0 else None


    def get_latest_version(self, id: str) -> MinerStatistics:
        params: tuple = (id,)
        result = self.db.select(SELECT, params)
        return self.map_row(result[0]) if len(result) > 0 else None


    def get(self, id: str, max_count: int = 99) -> list[tuple]:
        params: tuple = (id,)
        result = self.db.select(SELECT, params)
        return result[0:max_count] if len(result) >= max_count else result

#        with closing(self.__open()) as connection:
#            result = connection.cursor().execute(SELECT, (id,)).fetchall()
#            return result[0:max_count] if len(result) >= max_count else result


    def map_row(self, row: tuple) -> MinerStatistics:
        id: str = row[0]
        timestamp_s: int = row[1]
        block: int = row[2]
        super: int = row[3]
        xuni: int = row[4]
        cost: float = row[5]
        return MinerStatistics.create_with_timestamp(id, timestamp_s, block, super, xuni, cost)

    def __create_table(self):
        self.execute(CREATE_TABLE)


    def __insert(self, id: str, timestamp: int, block: int, sup: int, xuni: int, cost_ph: float):
#        with closing(self.connection.cursor()) as cursor:
#        self.connection.cursor().execute(INSERT, (id, timestamp, block, sup, xuni, cost_ph))
        self.db.insert(INSERT, (id, timestamp, block, sup, xuni, cost_ph))

#    def __update(self, id: int, hours: float, blocks: int, timestamp: float):
#        self.connection.cursor().execute(UPDATE, (hours, blocks, timestamp, id))

    def ________select(self, id: str) -> []:
#        with closing(self.connection.cursor()) as cursor:
        return self.db.select(SELECT, (id,))
#        result = self.connection.cursor().execute(SELECT, (id,)).fetchall()
#        return result if len(result) > 0 else []

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

