import psycopg2
import discord
import os
import datetime as dt
import logwrite as log

from typing import Callable, Any
from database.db_utils import *


SCRIPT_DIR = os.path.dirname(__file__)
BACKUP_PATH = os.path.join(SCRIPT_DIR, 'backup.sql')
DAILY_BACKUP_PATH = os.path.join(SCRIPT_DIR, 'daily_backup.sql')

class DatabaseHandler():
    """
    Represents an handler for the database.
    Allows to execute queries on the database

    Attributes
    ----------
    filename : str
        The filename which called the handler
    """
    def __init__(self, filename: str) -> None:
        try:
            conn = psycopg2.connect(
                host=os.getenv("host"),
                database=os.getenv("db_name"),
                user=os.getenv("db_user"),
                password=os.getenv("db_pwd")
            )

            log.writeLog(f" - Connection on the database for {filename} done - ")
        except psycopg2.Error as error:
            log.writeError(log.formatError(error))
            return

        self.conn = conn
        self.cursor = conn.cursor()


    def _error_handler(func: Callable):
        def wrapper(ref, *args):
            try:
                return func(ref, *args)
            except psycopg2.Error as dbError:
                ref: DatabaseHandler = ref
                ref.conn.rollback()
                raise dbError
            except Exception as commonError:
                raise commonError
        return wrapper


    def safeExecute(
        self,
        func: Callable[[Any], Any],
        *args
        ) -> Any:
        try:
            return func(*args)
        except Exception as e:
            log.writeError(log.formatError(e))
            

    def execute(self, query: str, raiseError: bool = False) -> str:
        if query.startswith("--") or query.startswith("\n") or len(query) == 0:
            return "Empty query"

        try:
            self.cursor.execute(query)
            self.conn.commit()

            try:
                return str(self.cursor.fetchall())
            except psycopg2.ProgrammingError as prgError:
                if raiseError:
                    raise prgError
                return "Query executed : nothing to fetch"

        except psycopg2.Error as commonError:
            self.conn.rollback()
            if raiseError:
                raise commonError
            return str(commonError)


    @_error_handler
    def backup(self, table: str, daily: bool = False) -> None:
        checkTable = f"AND table_name = '{table}'" if len(table) > 0 else None
        if table:
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'josix' %s;"
        else:
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'josix';"
            
        self.cursor.execute(query, (checkTable,))
        res = self.cursor.fetchall()

        file = DAILY_BACKUP_PATH if daily else BACKUP_PATH
        with open(file, "w") as f:
            f.write("-- Last backup : " + str(dt.datetime.now()) + "\n")
            for rowTable in res:
                table_name = rowTable[0]
                f.write("\n-- Records for table : josix." + table_name + "\n")

                self.cursor.execute("SELECT * FROM josix.%s" % (table_name))
                column_names = []
                columns_descr = self.cursor.description

                for c in columns_descr:
                    column_names.append(c[0])
                insert_prefix = 'INSERT INTO josix.%s (%s) VALUES ' % (table_name, ', '.join(column_names))
                rows = self.cursor.fetchall()

                for row in rows:
                    row_data = []
                    for rd in row:
                        if rd is None:
                            row_data.append('NULL')
                        elif isinstance(rd, dt.date):
                            row_data.append("'%s'" % (rd.strftime('%Y-%m-%d')))
                        elif isinstance(rd, dt.datetime):
                            row_data.append("'%s'" % (rd.strftime('%Y-%m-%d %H:%M:%S')))
                        else:
                            row_data.append(repr(rd))
                    f.write('%s (%s);\n' % (insert_prefix, ', '.join(row_data)))

    ###############
    # Getters
    ###############

    @_error_handler
    def getGuild(self, guildId: int) -> GuildDB | None:
        query = "SELECT * FROM josix.Guild WHERE idGuild = %s;"
        self.cursor.execute(query, (guildId,))
        res = self.cursor.fetchone()

        if res:
            return GuildDB(*res)
        return None

    @_error_handler
    def getUser(self, userId: int) -> UserDB | None:
        query = "SELECT * FROM josix.User WHERE idUser = %s;"
        self.cursor.execute(query, (userId,))
        res = self.cursor.fetchone()

        if res:
            return UserDB(*res)
        return None

    @_error_handler
    def getUsers(self, limit: int = 10) -> list[UserDB] | None:
        query = "SELECT * FROM josix.User LIMIT %s;"
        self.cursor.execute(query, (limit,))
        res = self.cursor.fetchall()
        if res:
            return [UserDB(row) for row in res]
        return None

    @_error_handler
    def getMsg(self, msgId: int) -> MsgReact | None:
        query = f"SELECT * FROM josix.Msgreact WHERE idMsg = %s;"
        self.cursor.execute(query, (msgId,))
        res = self.cursor.fetchone()

        if res:
            return MsgReact(*res)
        return None

    @_error_handler
    def getUserInGuild(self, userId: int, guildId: int) -> LinkUserGuild | None:
        query = """SELECT * FROM josix.UserGuild
                   WHERE idUser = %s AND idGuild  = %s;"""
        params = (userId, guildId)
        self.cursor.execute(query, params)
        res = self.cursor.fetchone()

        if res:
            return LinkUserGuild(*res)
        return None

    def getUserGuildLink(self, userId: int, guildId: int) -> tuple[UserDB | None, GuildDB | None, LinkUserGuild | None]:
        return (
            self.getUser(userId),
            self.getGuild(guildId),
            self.getUserInGuild(userId, guildId)
        )

    @_error_handler
    def getRoleFromReact(self, msgId: int, emojiName: str) -> int | None:
        query = """SELECT idRole FROM josix.ReactCouple rc
                   INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                   WHERE mc.idMsg = %s AND rc.nomEmoji = %s;"""
        params = (msgId, emojiName)
        self.cursor.execute(query, params)
        res = self.cursor.fetchone()
        if res:
            return res[0]
        return None

    @_error_handler
    def getCouples(self, msgId: int = None) -> list[ReactCouple] | None:
        if not msgId:
            query = """SELECT rc.idCouple, rc.nomEmoji, rc.idRole FROM josix.ReactCouple rc
                       INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple;"""
            params = ()
        else:
            query = """SELECT rc.idCouple, rc.nomEmoji, rc.idRole FROM josix.ReactCouple rc
                       INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                       WHERE mc.idMsg = %s;"""
            params = (msgId,)
        self.cursor.execute(query, params)
        self.cursor.execute(query, params)
        res = self.cursor.fetchall()
        if res:
            couples = []
            for row in res:
                couples.append(ReactCouple(*row))
            return couples
        return None

    @_error_handler
    def getCoupleFromRole(self, roleId: int) -> list[ReactCouple] | None:
        query = "SELECT * FROM josix.ReactCouple WHERE idRole = %s;"
        self.cursor.execute(query, (roleId,))
        res = self.cursor.fetchone()
        if res:
            couples = []
            for row in res:
                couples.append(ReactCouple(*row))
            return couples
        return None

    @_error_handler
    def getXpLeaderboard(self, guildId: int, limit: int) -> list[LinkUserGuild] | None:
        query = """SELECT * FROM josix.UserGuild
                   WHERE idGuild = %s
                   ORDER BY xp DESC
                   LIMIT %s"""
        params = (guildId, limit)
        self.cursor.execute(query, params)
        res = self.cursor.fetchall()
        if res:
            leaderboard = []
            for row in res:
                leaderboard.append(LinkUserGuild(*row))
            return leaderboard
        return None

    @_error_handler
    def getLeaderboardPos(self, userId: int, guildId: int) -> int | None:
        query = """SELECT COUNT(DISTINCT idUser) + 1
                   FROM josix.UserGuild
                   WHERE idGuild = %s AND
                         xp > (SELECT xp FROM josix.UserGuild WHERE idUser = %s AND idGuild = %s);"""
        params = (guildId, userId, guildId)
        self.cursor.execute(query, params)
        res = self.cursor.fetchone()
        if res:
            return res[0]
        return None

    @_error_handler
    def getNewsChanFromUser(self, userId: int) -> list[int] | None:
        query = """SELECT chanNews 
                   FROM josix.Guild g INNER JOIN josix.UserGuild ug ON g.idGuild = ug.idGuild
                   WHERE idUser = %s AND chanNews IS NOT NULL;"""
        self.cursor.execute(query, (userId,))
        res = self.cursor.fetchall()
        if res:
            ids = []
            for row in res:
                ids.append(row[0])
            return ids
        return None

    @_error_handler
    def checkBD(self, day: int, month: int) -> list[BirthdayAuto] | None:
        query = """SELECT u.idUser AS "user", ug.idGuild as "guild",
                          EXTRACT(DAY FROM u.hbDate) AS "day",
                          EXTRACT(MONTH FROM u.hbDate) AS "month"
                    FROM josix.User u INNER JOIN josix.UserGuild ug ON u.idUser = ug.idUser
                    WHERE EXTRACT(YEAR FROM u.hbDate) < EXTRACT(YEAR FROM NOW()) AND
                          EXTRACT(DAY FROM u.hbDate) = %s AND
                          EXTRACT(MONTH FROM u.hbDate) = %s;"""
        params = (day, month)
        self.cursor.execute(query, params)
        res = self.cursor.fetchall()
        if res:
            lstBD = []
            for row in res:
                lstBD.append(BirthdayAuto(*row))
        return None

    @_error_handler
    def getBDMonth(self, guildId: int, month: int) -> list[Birthday] | None:
        query = """SELECT u.idUser, EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate), 
                   FROM josix.User u INNER JOIN josix.UserGuild ug ON u.idUser = ug.idUser
                   WHERE ug.idGuild = %s AND EXTRACT(MONTH FROM u.hbDate) = %s
                   ORDER BY EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate);"""
        self.cursor.execute(query, (guildId, month))
        res = self.cursor.fetchall()
        if res:
            birthdays = []
            for row in res:
                birthdays.append(Birthday(*row))
            return birthdays
        return None


    @_error_handler
    def getGameFromUser(self, userId: int) -> Game | None:
        query = "SELECT * FROM josix.Games WHERE idUser = %s OR opponent = %s;"
        self.cursor.execute(query, (userId, userId))
        res = self.cursor.fetchone()

        if res:
            return Game(*res)
        return None

    @_error_handler
    def getGameType(self, gameName: str) -> GameType | None:
        query = "SELECT * FROM josix.GameType WHERE gameName = %s;"
        self.cursor.execute(query, (gameName,))
        res = self.cursor.fetchone()

        if res:
            return GameType(*res)
        return None

    @_error_handler
    def getExistingGame(self, gameId: int, userId: int) -> Game | None:
        query = """SELECT * FROM josix.Games
                   WHERE idGame = %s AND (idUser = %s OR opponent = %s);"""
        params = (gameId, userId, userId)
        self.cursor.execute(query, params)
        res = self.cursor.fetchone()

        if res:
            return Game(*res)
        return None

    def getSelectLogs(self, guildId: int) -> LogSelection | None:
        query = "SELECT * FROM josix.LogSelector WHERE idGuild = %s ORDER BY idLog;"
        self.cursor.execute(query, (guildId,))
        res = self.cursor.fetchall()

        if res:
            logs = []
            for row in res:
                logs.append(row[1])
            return LogSelection(guildId, logs)
        return None


    ###
    ###

    @_error_handler
    def getPlayerStat(self, userId: int) -> tuple[int, int] | None:
        query = "SELECT elo, nbGames FROM josix.User WHERE idUser = %s;"
        self.cursor.execute(query, (userId,))
        return self.cursor.fetchone()


    ###############
    # Adders
    ###############

    @_error_handler
    def addGuild(self, guildId: int, chanStat: int = 0, chanXP: int = 0) -> None:
        query = """INSERT INTO josix.Guild(idGuild, chanNews, xpNews)
                   VALUES (%s, %s, %s)"""
        params = (guildId, chanStat, chanXP)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def addMsg(self, guildId: int, msgId: int) -> None:
        query = "INSERT INTO josix.MsgReact VALUES(%s, %s);"
        params = (msgId, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def addCouple(self, couple: tuple, msgId: int) -> None:
        if len(couple) != 2:
            return
            
        query1 = """INSERT INTO josix.ReactCouple (nomEmoji, idRole)
                    VALUES (%s, %s) RETURNING idCouple;"""
        params = (couple[0], couple[1])
        self.cursor.execute(query1, params)
        idCouple = self.cursor.fetchone()[0]

        query2 = "INSERT INTO josix.MsgCouple VALUES (%s,%s);"
        params = (msgId, idCouple)
        self.cursor.execute(query2, params)
        self.conn.commit()

    @_error_handler
    def addUser(self, userId: int) -> None:
        query = "INSERT INTO josix.User (idUser) VALUES (%s);"
        self.cursor.execute(query, (userId,))
        self.conn.commit()

    @_error_handler
    def addUserGuild(self, userId: int, guildId: int) -> None:
        query = "INSERT INTO josix.UserGuild(idUser, idGuild) VALUES (%s, %s);"
        params = (userId, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def addDartLog(self, guildId: int, winner: discord.User, foes: tuple[discord.User]) -> None:
        text = ""
        for foe in foes:
            text += foe.name + "', '"
        text = text[0:len(text)-3]

        query = """INSERT INTO josix.DartLog (idGuild, winnerName, losersName)
                   VALUES (%s, %s, ARRAY[%s])"""
        params = (guildId, winner.name, text)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def addGameType(self, gameName: str) -> None:
        query = "INSERT INTO josix.GameType(gameName) VALUES(%s);"
        self.cursor.execute(query, (gameName,))
        self.conn.commit()

    @_error_handler
    def addGameFromId(self, typeId: int, userId:int, opponent: int = None) -> None:
        query = "INSERT INTO josix.Games(idType, idUser, opponent) VALUES(%s, %s, %s);"
        params = (typeId, userId, opponent)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def addGameFromName(self, gameName: str, userId:int, opponent: int = None) -> int | None:
        typeId = self.getGameType(gameName).id
        query = "INSERT INTO josix.Games(idType, idUser, opponent) VALUES(%s, %s, %s) RETURNING idGame;"
        params = (typeId, userId, opponent)
        self.cursor.execute(query, params)
        self.conn.commit()

        res = self.cursor.fetchone()
        if res:
            return res[0]
        return None


    ###############
    # Modifiers
    ###############

    @_error_handler
    def updatePlayerStat(self, userId: int, newElo: int) -> None:
        query = """UPDATE josix.User
                   SET elo = %s, nbGames = nbGames + 1
                   WHERE idUser = %s;"""
        params = (newElo, userId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def changeNewsChan(self, guildId: int, chanId: int) -> None:
        query = """UPDATE josix.Guild
                   SET chanNews = %s
                   WHERE idGuild = %s;"""
        params = (chanId, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def updateUserBD(self, userId: int, day: int, month: int, year: int) -> None:
        newBd = f"'{year}-{month}-{day}'"
        query = """UPDATE josix.User
                   SET hbDate = %s
                   WHERE idUser = %s;"""
        params = (newBd, userId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def resetBd(self, userId: int) -> None:
        query = """UPDATE josix.User
                   SET hbDate = hbDate - INTERVAL '1 year'
                   WHERE idUser = %s;"""
        self.cursor.execute(query, (userId,))
        self.conn.commit()

    @_error_handler
    def updateUserXP(self, userId: int, guildId: int, lvl: int, xp: int, lastSend: dt.datetime) -> None:
        query = """UPDATE josix.UserGuild
                   SET lvl = %s,
                       xp = %s,
                       lastMessage = %s
                    WHERE idUser = %s AND idGuild = %s;"""
        params = (lvl, xp, lastSend, userId, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def changeXPChan(self, guildId: int, chanId: int) -> None:
        query = """UPDATE josix.Guild
                   SET xpNews = %s
                   WHERE idGuild = %s;"""
        params = (chanId, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def updateGuildXpEnabled(self, guildId: int) -> None:
        query = """UPDATE josix.Guild
                   SET enableXP = NOT enableXP
                   WHERE idGuild = %s"""
        self.cursor.execute(query, (guildId,))
        self.conn.commit()

    @_error_handler
    def updateUserBlock(self, userId: int, guildId: int) -> None:
        query = """UPDATE josix.UserGuild
                   SET xpBlocked = NOT xpBlocked
                   WHERE idUser = %s AND idGuild = %s;"""
        params = (userId, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def updateWelcomeGuild(self, guildId: int, chanId: int | None, roleId: int | None, message: str) -> None:
        if not chanId:
            chanId = 0
        if not roleId:
            roleId = 0

        query = """UPDATE josix.Guild
                   SET enableWelcome = TRUE,
                       welcomeChan = %s,
                       welcomeRole = %s,
                       welcomeText = %s
                   WHERE idGuild = %s;"""
        params = (chanId, roleId, message, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def updateGuildWelcomeEnabled(self, guildId: int) -> None:
        query = """UPDATE josix.Guild
                   SET enableWelcome = NOT enableWelcome
                   WHERE idGuild = %s"""
        self.cursor.execute(query, (guildId,))
        self.conn.commit()

    @_error_handler
    def updateLogSelects(self, guildId: int, logs: list[int]) -> None:
        for i in range(1, 13):
            params = (guildId, i)

            if i in logs:
                query = "INSERT INTO josix.LogSelector VALUES(%s, %s) ON CONFLICT DO NOTHING;"
            else:
                query = "DELETE FROM josix.LogSelector WHERE idGuild = %s AND idLog = %s;"
            self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def updateLogsEntries(self, logs: list[tuple[str, int]]) -> None:
        for log in logs:
            query = "INSERT INTO josix.Logs VALUES(%s, %s) ON CONFLICT DO NOTHING;"
            params = (log[1], log[0])
            self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def updateLogChannel(self, guildId: int, channelId: int | None) -> None:
        query = "UPDATE josix.Guild SET logNews = %s WHERE idGuild = %s;"
        params = (channelId, guildId)
        self.cursor.execute(query, params)
        self.conn.commit()

    ###############
    # Deleters
    ###############

    @_error_handler
    def delMessageReact(self, msgId: int) -> None:
        query = "DELETE FROM josix.MsgCouple WHERE idMsg = %s;"
        query2 = "DELETE FROM josix.MsgReact WHERE idMsg = %s;"
        self.cursor.execute(query, (msgId,))
        self.cursor.execute(query2, (msgId,))
        self.conn.commit()

    @_error_handler
    def delReactCouple(self, coupleId: int) -> None:
        query = "DELETE FROM josix.MsgCouple WHERE idCouple = %s;"
        query2 = "DELETE FROM josix.ReactCouple WHERE idCouple = %s;"
        self.cursor.execute(query, (coupleId,))
        self.cursor.execute(query2, (coupleId,))
        self.conn.commit()

    @_error_handler
    def delMessageCouple(self, msgId: int, coupleId: int) -> None:
        query = "DELETE FROM josix.MsgCouple WHERE idMsg = %s AND idCouple = %s;"
        params = (msgId, coupleId)
        self.cursor.execute(query, params)
        self.conn.commit()

    @_error_handler
    def quitGame(self, userId: int) -> None:
        query = "DELETE FROM josix.Games WHERE idUser = %s OR opponent = %s;"
        self.cursor.execute(query, (userId, userId))
        self.conn.commit()

    @_error_handler
    def deleteGame(self, gameId: int) -> None:
        query = "DELETE FROM josix.Games WHERE idGame = %s;"
        self.cursor.execute(query, (gameId,))
        self.conn.commit()

    @_error_handler
    def deleteGames(self) -> None:
        query = "DELETE FROM josix.Games;"
        self.cursor.execute(query)
        self.conn.commit()