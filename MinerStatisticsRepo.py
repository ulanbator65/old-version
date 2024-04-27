
from contextlib import closing
from datetime import datetime
from sqlite3 import Connection

from DbManager import DbManager
from config import DB_NAME


class MinerStatisticsRepo:
    def __init__(self, db_man: DbManager = DbManager(DB_NAME)):
        self.db: DbManager = db_man
        self.connection: Connection = None
#        print(json)
#        self.db = "database.db"
#        self.db = sqlite3.connect("database.db")

        with closing(self.__open()) as connection:
            self.__create_table()
            self.connection.commit()


    def create(self, id: str, hours: float, blocks: int):
        with closing(self.__open()) as connection:
            self.__insert(id, hours, blocks)
            self.connection.commit()


    def update(self, id: str, hours: float, blocks: int):
        norm = hours if hours > 0.0 else 0.0

        with closing(self.__open()) as connection:

            if not self.__select(id):
                self.__insert(id, norm, blocks, datetime.now().timestamp())
            else:
                self.__update(id, norm, blocks, datetime.now().timestamp())
            self.connection.commit()


    def get(self, id: str):
        with closing(self.__open()) as connection:
            result = connection.cursor().execute("SELECT * FROM miner WHERE id = ?", (id,)).fetchall()
            return result[0] if len(result) > 0 else None
#            r = self.__select(instance_id)
#            return r


    def __create_table(self):
        sql = "CREATE TABLE IF NOT EXISTS miner (id STRING PRIMARY KEY, hours NUMBER, blocks INTEGER, timestamp STRING)"
        self.execute(sql)

    def __insert(self, id: str, hours: float, blocks: int, timestamp: float):
#        with closing(self.connection.cursor()) as cursor:
        self.connection.cursor().execute("INSERT INTO miner VALUES(?, ?, ?, ?)", (id, hours, blocks, timestamp))

    def __update(self, id: str, hours: float, blocks: int, timestamp: float):
#        with closing(self.connection.cursor()) as cursor:
        self.connection.cursor().execute("UPDATE miner SET hours=?, blocks=?, timestamp=? WHERE id=?", (hours, blocks, timestamp, id))

    def __select(self, id: str) -> tuple:
#        with closing(self.connection.cursor()) as cursor:
        result = self.connection.cursor().execute("SELECT * FROM miner WHERE id = ?", (id,)).fetchall()
        return result[0] if len(result) > 0 else None

    def __delete(self, id: str):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("DELETE FROM miner WHERE id=?", id)

    def delete_all(self):
        with closing(self.__open()) as connection:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute("DELETE FROM miner")
            self.connection.commit()

    def execute(self, sql: str):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql)
        self.connection.commit()

    def __open(self):
        self.connection = self.db.open()
        return self.connection

