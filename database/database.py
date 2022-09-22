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

    def getUsers(self, limit : int = 10) -> list:
        query = "SELECT * FROM josix.User LIMIT %s;"
        params = (limit,)
        self.cursor.execute(query, params)
        print(self.cursor.fetchall())

    def getMsg(self, msgId : int):
        query = f"SELECT * FROM josix.Msgreact WHERE idMsg = {msgId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getRoleFromReact(self, msgId : int, emojiName : str):
        query = f"""SELECT idRole FROM josix.ReactCouple rc
                    INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                    WHERE mc.idMsg = {msgId} AND rc.nomEmoji = '{emojiName}';"""
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getCouples(self, msgId : int = None) -> list:
        if not msgId:
            query = f"""SELECT rc.nomEmoji AS "name", rc.idRole AS "idRole" FROM josix.ReactCouple rc
                        INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple;"""
        else:
            query = f"""SELECT rc.nomEmoji AS "name", rc.idRole AS "idRole" FROM josix.ReactCouple rc
                        INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                        WHERE mc.idMsg = {msgId};"""
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def addMsg(self, guildId : int, msgId : int) -> None:
        query = f"INSERT INTO josix.MsgReact VALUES({msgId},{guildId});"
        self.cursor.execute(query)
        self.conn.commit()

    def addCouple(self, couple : tuple, msgId : int) -> None:
        if len(couple) != 2:
            return
            
        query1 = f"INSERT INTO josix.ReactCouple (nomEmoji, idRole) VALUES ('{couple[0]}',{couple[1]}) RETURNING idCouple;"
        self.cursor.execute(query1)
        idCouple = self.cursor.fetchone()[0]

        query2 = f"INSERT INTO josix.MsgCouple VALUES ({msgId},{idCouple});"
        self.cursor.execute(query2)
        self.conn.commit()
