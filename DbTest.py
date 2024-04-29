
from contextlib import closing
from datetime import datetime
from sqlite3 import Connection

from Field import Field
from constants import *
from DbManager import DbManager
from config import DB_NAME

INSERT = "INSERT INTO test VALUES(?, ?, ?, ?)"
UPDATE = "UPDATE test SET hours=?, blocks=?, timestamp=? WHERE id=?"
SELECT = "SELECT * FROM test WHERE id = ?"
SELECT_ALL = "SELECT * FROM test"
DELETE = "DELETE FROM test WHERE id = ?"
CREATE_TABLE = "CREATE TABLE IF NOT EXISTS test (id STRING PRIMARY KEY, hours NUMBER, blocks INTEGER, timestamp STRING)"

fgreen = Field(GREEN)


class DbTest:

    def __init__(self, db_man: DbManager = DbManager(DB_NAME)):
        self.db: DbManager = db_man
        self.connection: Connection = None
#        print(json)
#        self.db = "database.db"
#        self.db = sqlite3.connect("database.db")

        with closing(self.__open()) as connection:
            self.__create_table()
#            self.connection.commit()


    def run_test(self):
        all2 = self.db.select_all(SELECT_ALL)
        print(all2)
        if len(all2) > 1:
            raise Exception("Test failed: ", all2)

        self.update(str(1111), 0, 0)
        self.update(str(1111), 1, 2)

        test = self.get(str(1111))
        if int(test[0]) != 1111 or test[1] != 1:
            raise Exception("Test failed: ", test)

        print(fgreen.format("Integration tests completed successfully!"))


    def create(self, id: str, hours: float, blocks: int):
        params: tuple = (id, hours, blocks, int(datetime.now().timestamp()))

        self.db.insert(INSERT, params)


    def update(self, id: str, hours: float, blocks: int):
        params: tuple = (hours, blocks, int(datetime.now().timestamp()), id)

        row = self.get(id)
        if not row:
            self.create(id, hours, blocks)
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
        self._execute(CREATE_TABLE)


    def delete_all(self):
        with closing(self.__open()) as connection:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute("DELETE FROM miner")
            self.connection.commit()

    def _execute(self, sql: str):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql)
        self.connection.commit()

    def __open(self):
        self.connection = self.db.open()
        return self.connection

