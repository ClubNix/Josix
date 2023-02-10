import psycopg2
import discord
import os
import datetime
import logwrite as log


SCRIPT_DIR = os.path.dirname(__file__)
FILE_PATH = os.path.join(SCRIPT_DIR, 'backup.sql')

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
        except psycopg2.Error as error:
            log.writeError(log.formatError(error))
            return

        self.conn = conn
        self.cursor = conn.cursor()

    def execute(self, query: str) -> str:
        try:
            self.cursor.execute(query)
            self.conn.commit()

            try:
                return str(self.cursor.fetchall())
            except psycopg2.ProgrammingError:
                return "Query executed : nothing to fetch"

        except psycopg2.Error as error:
            self.conn.rollback()
            return str(error)

    def backup(self):
        self.cursor.execute("SELECT * FROM information_schema.tables WHERE table_schema = 'josix';")
        res = self.cursor.fetchall()

        with open(FILE_PATH, "w") as f:
            for row in res:
                table_name = row[2]
                f.write("\n-- Records for table : josix." + table_name + "\n")

                self.cursor.execute("SELECT * FROM josix.%s" % (table_name))  # change the query according to your needs
                column_names = []
                columns_descr = self.cursor.description

                for c in columns_descr:
                    column_names.append(c[0])
                insert_prefix = 'INSERT INTO josix.%s (%s) VALUES ' % (table_name, ', '.join(column_names))
                rows = self.cursor.fetchall()

                row_data = []
                for row in rows:
                    for rd in row:
                        if rd is None:
                            row_data.append('NULL')
                        elif isinstance(rd, datetime.date):
                            row_data.append("'%s'" % (rd.strftime('%Y-%m-%d')))
                        elif isinstance(rd, datetime.datetime):
                            row_data.append("'%s'" % (rd.strftime('%Y-%m-%d %H:%M:%S')))
                        else:
                            row_data.append(repr(rd))

                # this is the text that will be put in the SQL file. You can change it if you wish.
                f.write('%s (%s);\n' % (insert_prefix, ', '.join(row_data)))


    ###############
    ############### Getters
    ###############


    def getGuild(self, guildId: int) -> tuple:
        query = f"SELECT * FROM josix.Guild WHERE idGuild = {guildId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getUser(self, userId: int) -> tuple:
        query = f"SELECT * FROM josix.User WHERE idUser = {userId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getUsers(self, limit: int = 10) -> list:
        query = "SELECT * FROM josix.User LIMIT %s;"
        params = (limit,)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def getPlayerStat(self, userId: int) -> tuple:
        query = f"SELECT elo, nbGames FROM josix.User WHERE idUser = {userId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getMsg(self, msgId: int) -> tuple:
        query = f"SELECT * FROM josix.Msgreact WHERE idMsg = {msgId};"
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getRoleFromReact(self, msgId: int, emojiName: str) -> tuple:
        query = f"""SELECT idRole FROM josix.ReactCouple rc
                    INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                    WHERE mc.idMsg = {msgId} AND rc.nomEmoji = '{emojiName}';"""
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def getCouples(self, msgId: int = None) -> list:
        if not msgId:
            query = f"""SELECT rc.nomEmoji AS "name", rc.idRole AS "idRole" FROM josix.ReactCouple rc
                        INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple;"""
        else:
            query = f"""SELECT rc.nomEmoji AS "name", rc.idRole AS "idRole" FROM josix.ReactCouple rc
                        INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                        WHERE mc.idMsg = {msgId};"""
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def getUserInGuild(self, userId: int, guildId: int) -> tuple:
        query = f"""SELECT idUser AS "user", idGuild AS "guild" FROM josix.UserGuild
                    WHERE idUser = {userId} AND idGuild  = {guildId};"""
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def checkBD(self, day: int, month: int) -> list:
        query = f"""SELECT u.idUser AS "user", ug.idGuild as "guild",
                           EXTRACT(MONTH FROM u.hbDate) AS "month",
                           EXTRACT(DAY FROM u.hbDate) AS "day"
                    FROM josix.User u INNER JOIN josix.UserGuild ug ON u.idUser = ug.idUser
                    WHERE EXTRACT(YEAR FROM u.hbDate) < EXTRACT(YEAR FROM NOW()) AND
                          EXTRACT(DAY FROM u.hbDate) = {day} AND
                          EXTRACT(MONTH FROM u.hbDate) = {month};"""
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def getNewsChan(self, userId: int) -> list:
        query = f"""SELECT chanNews FROM josix.Guild g
                                    INNER JOIN josix.UserGuild ug ON g.idGuild = ug.idGuild
                    WHERE idUser = {userId} AND chanNews IS NOT NULL;"""
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def getBirthdays(self, guildId: int) -> list:
        query = f"""SELECT EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate)
                    FROM josix.User u INNER JOIN josix.UserGuild ug ON u.idUser = ug.idUser
                    WHERE ug.idGuild = {guildId}
                    ORDER BY EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate);"""
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def getBDMonth(self, guildId: int, month: int) -> list:
        query = f"""SELECT EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate), u.idUser
                    FROM josix.User u INNER JOIN josix.UserGuild ug ON u.idUser = ug.idUser
                    WHERE ug.idGuild = {guildId} AND EXTRACT(MONTH FROM u.hbDate) = {month}
                    ORDER BY EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate);"""
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def getBDUser(self, userId: int) -> tuple:
        query = f"""SELECT hbDate FROM josix.User WHERE idUser = {userId};"""
        self.cursor.execute(query)
        return self.cursor.fetchone()

    ###############
    ############### Adders
    ###############

    def addGuild(self, guildId: int, chanStat: int = 0, nbMembers: int = 0, status: int = 0):
        query = f"INSERT INTO josix.Guild(idGuild, totalMember, sendStatus, chanNews) VALUES({guildId},{nbMembers},'{status}',{chanStat})"
        self.cursor.execute(query)
        self.conn.commit()

    def addMsg(self, guildId: int, msgId: int) -> None:
        query = f"INSERT INTO josix.MsgReact VALUES({msgId},{guildId});"
        self.cursor.execute(query)
        self.conn.commit()

    def addCouple(self, couple: tuple, msgId: int) -> None:
        if len(couple) != 2:
            return
            
        query1 = f"INSERT INTO josix.ReactCouple (nomEmoji, idRole) VALUES ('{couple[0]}',{couple[1]}) RETURNING idCouple;"
        self.cursor.execute(query1)
        idCouple = self.cursor.fetchone()[0]

        query2 = f"INSERT INTO josix.MsgCouple VALUES ({msgId},{idCouple});"
        self.cursor.execute(query2)
        self.conn.commit()

    def addUser(self, userId: int) -> None:
        query = f"INSERT INTO josix.User (idUser, elo, nbGames) VALUES ({userId}, 1000, 0);"
        self.cursor.execute(query)
        self.conn.commit()

    def addUserGuild(self, userId: int, guildId: int) -> None:
        query = f"""INSERT INTO josix.UserGuild(idUser, idGuild) VALUES ({userId},{guildId});"""
        self.cursor.execute(query)
        self.conn.commit()

    def addDartLog(self, guildId: int, winner: discord.User, foes: tuple[discord.User]):
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

    def updatePlayerStat(self, userId: int, newElo: int) -> None:
        query = f"""UPDATE josix.User
                    SET elo = {newElo}, nbGames = nbGames + 1
                    WHERE idUser = {userId};"""
        self.cursor.execute(query)
        self.conn.commit()

    def changeNewsChan(self, guildId: int, chanId: int) -> None:
        query = f"""UPDATE josix.Guild
                    SET chanNews = {chanId}
                    WHERE idGuild = {guildId};"""
        self.cursor.execute(query)
        self.conn.commit()

    def updateUserBD(self, userId: int, day: int, month: int, year: int) -> None:
        newBd = f"'{year}-{month}-{day}'"
        query = f"""UPDATE josix.User
                    SET hbDate = {newBd}
                    WHERE idUser = {userId};"""
        self.cursor.execute(query)
        self.conn.commit()

    def resetBd(self, userId: int) -> None:
        query = f"""UPDATE josix.User
                    SET hbDate = hbDate - INTERVAL '1 year'
                    WHERE idUser = {userId};"""
        self.cursor.execute(query)
        self.conn.commit()

    ###############
    ############### Deleters
    ###############

    def delMsg(self, msgId: int) -> None:
        query = f"DELETE FROM MsgReact WHERE idMsg = {msgId};"
        self.cursor.execute(query)
        self.conn.commit()