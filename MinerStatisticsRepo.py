
from contextlib import closing
from datetime import datetime
from sqlite3 import Connection

from DbManager import DbManager
from config import DB_NAME

INSERT = "INSERT INTO miner VALUES(?, ?, ?, ?)"
UPDATE = "UPDATE miner SET hours=?, blocks=?, timestamp=? WHERE id=?"
SELECT = "SELECT * FROM miner WHERE id = ?"
DELETE = "DELETE FROM miner WHERE id=?"


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
        params: tuple = (id, hours, blocks, int(datetime.now().timestamp()))

        self.db.insert(INSERT, params)


    def update(self, id: str, hours: float, blocks: int):
        params: tuple = (id, hours, blocks, int(datetime.now().timestamp()))

        if hours < 0.001:
            raise Exception("WTF!!!")

        row = self.get(id)
        if not row:
            self.db.insert(INSERT, params)
        else:
            self.db.update(UPDATE, params)


    def get(self, id: str):
        params: tuple = (id,)
        result = self.db.select(SELECT, params)

        if len(result) > 1:
            print(result)
            raise Exception("WTF!!!")

        return result[0] if len(result) > 0 else None

#        with closing(self.__open()) as connection:
#            result = connection.cursor().execute("SELECT * FROM miner WHERE id = ?", (id,)).fetchall()
#            return result[0] if len(result) > 0 else None


    def __create_table(self):
        sql = "CREATE TABLE IF NOT EXISTS miner (id STRING PRIMARY KEY, hours NUMBER, blocks INTEGER, timestamp STRING)"
        self.execute(sql)


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

