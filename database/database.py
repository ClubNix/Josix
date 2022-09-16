import psycopg2 
import os

class DatabaseHandler():
    def __init__(self) -> None:
        try:
            conn = psycopg2.connect(
                host="localhost",
                database=os.getenv("db_name"),
                user=os.getenv("db_user"),
                password=os.getenv("db_pwd")
            )

            print("Connection realized ***** ", end="")
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error on connection ***** ", end="")
            print(error)
            exit(1)

        self.conn = conn
        self.cursor = conn.cursor()

    def getUsers(self, limit : int = 10):
        query = "SELECT * FROM josix.User LIMIT %s;"
        params = (limit,)
        self.cursor.execute(query, params)
        print(self.cursor.fetchall())