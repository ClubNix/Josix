from josix import cnx

class DatabaseHandler():
    def __init__(self) -> None:
        self.conn = cnx
        self.cursor = cnx.cursor()

    def getUsers(self, limit : int = 10):
        query = "SELECT * FROM josix.User LIMIT %s;"
        params = (limit,)
        self.cursor.execute(query, params)
        print(self.cursor.fetchall())