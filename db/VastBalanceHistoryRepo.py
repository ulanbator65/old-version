
from sqlite3 import Connection

from db.DbManager import DbManager
from config import HISTORY_DB
from Field import Field
from constants import *

CREATE_TABLE = "CREATE TABLE IF NOT EXISTS vast_balance_history (timestamp INTEGER PRIMARY KEY, balance NUMBER)"
SELECT = "SELECT * FROM vast_balance_history WHERE timestamp = ?;"
SELECT_FROM_TIMESTAMP = "SELECT * FROM vast_balance_history WHERE timestamp > ? ORDER BY timestamp DESC;"
SELECT_ALL = "SELECT * FROM vast_balance_history;"
INSERT = "INSERT INTO vast_balance_history VALUES(?, ?)"
DELETE = "DELETE FROM vast_balance_history WHERE timestamp = ?"
DELETE_ON_TIMESTAMP_OLDER_THAN = "DELETE FROM vast_balance_history WHERE timestamp < ?"
DELETE_ALL = "DELETE FROM vast_balance_history"

error = Field(RED)

# "ALTER TABLE miner_history ADD new_column_name column_definition;"


class VastBalanceHistoryRepo:
    def __init__(self, db_man: DbManager = DbManager(HISTORY_DB)):
        self.db: DbManager = db_man
        self.connection: Connection = None

        self.db.execute(CREATE_TABLE)


    def get_nr_of_rows(self):
        pass


    def create(self, timestamp_s: int, balance: float) -> bool:

        params: tuple = (timestamp_s, balance)
        return self.db.insert(INSERT, params)


    def get(self, timestamp: int) -> float:
        params: tuple = (timestamp,)
        result: list[tuple] = self.db.select(SELECT, params)
        row = result[0]
        return row[1]


    def get_all(self) -> list[tuple]:
        return self.db.execute(SELECT_ALL)


    def get_from_timestamp(self, timestamp: int) -> list[tuple]:

        params: tuple = (timestamp,)
        return self.db.select(SELECT_FROM_TIMESTAMP, params)
#        return list(map(lambda x: x[1], result))


    def delete(self, timestamp: int):
        params: tuple = (timestamp,)
        self.db.execute_statement(DELETE, params)


    def __delete_older_than(self, timestamp: int):
        params: tuple = (timestamp,)
        self.db.delete(DELETE_ON_TIMESTAMP_OLDER_THAN, params)

    def delete_all(self):
        self.db.execute(DELETE_ALL)

