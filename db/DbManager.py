
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

    def select_all(self, sql: str) -> list:
        with closing(self._open()) as connection:
            return connection.cursor() \
                .execute(sql).fetchall()

    def insert(self, prepared_statement: str, params: tuple) -> bool:
        with closing(self._open()) as connection:
            connection.cursor().execute(prepared_statement, params)
            connection.commit()
        return True


    def update(self, prepared_statement: str, params: tuple):
        with closing(self._open()) as connection:
            connection.cursor().execute(prepared_statement, params)
            connection.commit()


    def delete(self, prepared_statement: str, params: tuple):
        with closing(self._open()) as connection:
            connection.cursor().execute(prepared_statement, params)
            connection.commit()


    def execute(self, sql: str):
        result = None
        with closing(self._open()) as connection:
            result = connection.cursor().execute(sql).fetchall()
            connection.commit()

        return result


    def execute_statement(self, prepared_statement: str, params: tuple):
        result = None
        with closing(self._open()) as connection:
            result = connection.cursor().execute(prepared_statement, params).fetchall()
            connection.commit()

        return result


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

