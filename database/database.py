import psycopg2
import discord
import os

import logwrite as log

class DatabaseHandler():
    def __init__(self) -> None:
        try:
            conn = psycopg2.connect(
                host=os.getenv("host"),
                database=os.getenv("db_name"),
                user=os.getenv("db_user"),
                password=os.getenv("db_pwd")
            )

            log.writeLog(" - Connection on the database done - ")
        except (Exception, psycopg2.DatabaseError, psycopg2.OperationalError) as error:
            log.writeError(log.formatError(error))
            return

        self.conn = conn
        self.cursor = conn.cursor()

    ###############
    ############### Getters
    ###############

    def getUsers(self, limit : int = 10) -> list:
        query = "SELECT * FROM josix.User LIMIT %s;"
        params = (limit,)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def getUser(self, userId : int) -> tuple:
        query = f"SELECT * FROM josix.User WHERE idUser = {userId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getPlayerStat(self, userId : int) -> tuple:
        query = f"SELECT elo, nbGames FROM josix.User WHERE idUser = {userId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getMsg(self, msgId : int) -> tuple:
        query = f"SELECT * FROM josix.Msgreact WHERE idMsg = {msgId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getRoleFromReact(self, msgId : int, emojiName : str) -> tuple:
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

    ###############
    ############### Adders
    ###############

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

    def addUser(self, userId) -> None:
        query = f"INSERT INTO josix.User (idUser, elo, nbGames) VALUES ({userId}, 1000, 0);"
        self.cursor.execute(query)
        self.conn.commit()

    def addDartLog(self, guildId : int, winner : discord.User, foes : tuple[discord.User]):
        text = ""
        for foe in foes:
            text += foe.name + "', '"
        text = text[0:len(text)-3]

        query = f"INSERT INTO josix.DartLog (idGuild, winnerName, losersName) VALUES({guildId}, '{winner.name}', ARRAY['{text}])"
        self.cursor.execute(query)
        self.conn.commit()

    ###############
    ############### Modifiers
    ###############

    def updatePlayerStat(self, userId : int, newElo : int) -> None:
        query = f"""UPDATE josix.User
                    SET elo = {newElo}, nbGames = nbGames + 1
                    WHERE idUser = {userId};"""
        self.cursor.execute(query)
        self.conn.commit()
