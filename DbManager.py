
from contextlib import closing
import sqlite3
from sqlite3 import Connection


class DbManager:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = None


    def open(self) -> Connection:
        return sqlite3.connect(self.db_name)


    def select(self, prepared_statement: str, params: tuple) -> list:
        with closing(self._open()) as connection:
            return connection.cursor()\
                .execute(prepared_statement, params).fetchall()


    def insert(self, prepared_statement: str, params: tuple):
        print("insert2: ", params)
        with closing(self._open()) as connection:
            connection.cursor().execute(prepared_statement, params)
            connection.commit()

    def update(self, prepared_statement: str, params: tuple):
        print("update2: ", params)
        with closing(self._open()) as connection:
            connection.cursor().execute(prepared_statement, params)
            connection.commit()

    def _open(self):
        self.connection = self.open()
        return self.connection


    def __del__(self):
        """
        When destroying the object, it is necessary to commit changes
        in the database and close the connection
        """
        try:
            connection = self.open()
            connection.commit()
            connection.close()
        except:
            print("---- Error closing database")

