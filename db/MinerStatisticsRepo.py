
from datetime import datetime
from sqlite3 import Connection

from db.DbManager import DbManager
from config import DB_NAME

INSERT = "INSERT INTO miner VALUES(?, ?, ?, ?, ?)"
UPDATE = "UPDATE miner SET hours=?, blocks=?, xuni=?, timestamp=? WHERE id=?"
SELECT = "SELECT * FROM miner WHERE id = ?"
DELETE = "DELETE FROM miner WHERE id=?"
CREATE_TABLE = "CREATE TABLE IF NOT EXISTS miner (id STRING PRIMARY KEY, hours NUMBER, blocks INTEGER, xuni INTEGER, timestamp STRING)"


class MinerStatisticsRepo:

    def __init__(self, db_man: DbManager = DbManager(DB_NAME)):
        self.db: DbManager = db_man
        self.connection: Connection = None

        self.db.execute(CREATE_TABLE)


    def create(self, id: str, hours: float, blocks: int):
        params: tuple = (id, hours, blocks, 0, int(datetime.now().timestamp()))

        self.db.insert(INSERT, params)


    def update(self, id: str, hours: float, blocks: int):
        # Note!!!  ID must be last in the tuple for the 'where' clause to work
        params: tuple = (hours, blocks, 0, int(datetime.now().timestamp()), id)

        if hours < 0.001:
            raise Exception("WTF!!!")

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


    def delete_all(self):
        self.db.execute("DELETE FROM miner")

