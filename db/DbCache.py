
from datetime import datetime
from sqlite3 import Connection

from db.DbManager import DbManager
from config import CACHE_DB

INSERT = "INSERT INTO cache VALUES(?, ?, ?)"
UPDATE = "UPDATE cache SET timestamp=?, value=?  WHERE key=?"
SELECT = "SELECT * FROM cache WHERE key = ?"
DELETE = "DELETE FROM cache WHERE key = ?"
CREATE_TABLE = "CREATE TABLE IF NOT EXISTS cache (key STRING PRIMARY KEY, timestamp STRING, value STRING)"


class DbCache:

    def __init__(self, db_man: DbManager = DbManager(CACHE_DB)):
        self.db: DbManager = db_man
        self.connection: Connection = None

        self.db.execute(CREATE_TABLE)


    def create(self, key: str, value: str):
        params: tuple = (key, int(datetime.now().timestamp()), value)

        self.db.insert(INSERT, params)


    def update(self, key: str, value: str):
        # Note!!!  ID must be last in the tuple for the 'where' clause to work
        params: tuple = (int(datetime.now().timestamp()), value, key)

        existing_value = self.get(key)
        if not existing_value:
            self.create(key, value)
        else:
            self.db.update(UPDATE, params)


    def get(self, key: str) -> tuple:
        params: tuple = (key,)
        result = self.db.select(SELECT, params)

        if len(result) > 1:
            print(result)
            raise Exception("WTF!!!")

        return result[0] if len(result) > 0 else None


    def delete_all(self):
        self.db.execute("DELETE FROM cache")

