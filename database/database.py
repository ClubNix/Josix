#mysql -h localhost -u root -p

import discord
import mysql.connector
from mysql.connector import errorcode
import database.singleton as sgl

class DatabaseHandler(metaclass = sgl.Singleton):
    def __init__(self, user : str,
                       password : str,
                       host : str,
                       database : str):

        try:
            cnx = mysql.connector.connect(user = user,
                                          password = password,
                                          host = host,
                                          database = database)

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with the username or/and password")

            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")

            elif err.errno == errorcode.CR_UNKNOWN_HOST:
                print("Unknown host")

            else:
                print(err)
        else:
            print("-------------------------------------- \nBot successfully connected to database \n-------------------------------------- \n")
            cursor = cnx.cursor()

        self.cursor = cursor
        self.cnx = cnx

    def executeQ(self, query : str, data : tuple = None):
        if data == None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, data)
        self.cnx.commit()

    def commitQ(self):
        self.cnx.commit()


    ###############
    ###############
    ############### Select
    ###############
    ############### 


    def getUser(self, id : int) -> list:
        self.cursor.execute(f"SELECT * FROM User Where idUser = {id};")
        return self.cursor.fetchall()

    def getGuild(self, id : int) -> list:
        self.cursor.execute(f"SELECT * FROM Guild Where idGuild = {id};")
        return self.cursor.fetchall()

    def getChannel(self, id : int) -> list:
        self.cursor.execute(f"SELECT * FROM Channel Where idChannel = {id};")
        return self.cursor.fetchall()

    def getReact(self, id : int) -> list:
        self.cursor.execute(f"SELECT * FROM Reaction Where idReact = {id};")
        return self.cursor.fetchall()

    def getReactGuild(self, id : int) -> list:
        self.cursor.execute(f"SELECT * FROM Reaction Where idGuild = {id};")
        return self.cursor.fetchall()

    def getBG(self, id : int, target : int, id2 : int = None) -> list:
        if target == 0:
            self.cursor.execute(f"SELECT * FROM BelongG Where idUser = {id};")
        elif target == 1:
            self.cursor.execute(f"SELECT * FROM BelongG Where idGuild = {id};")
        elif target == 2:
            self.cursor.execute(f"SELECT * FROM BelongG Where idUser = {id} AND idGuild = {id2};")
        return self.cursor.fetchall()

    def getBC(self, id : int, target : int, id2 : int = None) -> list:
        if target == 0:
            self.cursor.execute(f"SELECT * FROM BelongC Where idUser = {id};")
        elif target == 1:
            self.cursor.execute(f"SELECT * FROM BelongC Where idChannel = {id};")
        elif target == 2:
            self.cursor.execute(f"SELECT * FROM BelongC Where idUser = {id} AND idChannel = {id2};")
        return self.cursor.fetchall()


    ###############
    ###############
    ############### Delete
    ###############
    ###############


    def deleteUser(self, id : int):
        self.cursor.execute(f"DELETE FROM BelongC WHERE idUser = {id};")
        self.cursor.execute(f"DELETE FROM BelongG WHERE idUser = {id};")
        self.cursor.execute(f"DELETE FROM User WHERE idUser = {id};")
        self.cnx.commit()

    def deleteGuild(self, id : int):
        self.cursor.execute(f"DELETE FROM BelongG WHERE idGuild = {id};")
        self.cursor.execute(f"DELETE FROM Channel WHERE idGuild = {id};")
        self.cursor.execute(f"DELETE FROM Reaction WHERE idGuild = {id};")
        self.cursor.execute(f"DELETE FROM Guild WHERE idGuild = {id};")
        self.cnx.commit()

    def deleteChannel(self, id : int):
        self.cursor.execute(f"DELETE FROM BelongC WHERE idChannel = {id};")
        self.cursor.execute(f"DELETE FROM Channel WHERE idChannel = {id};")
        self.cnx.commit()

    def deleteReact(self, id : int):
        self.cursor.execute(f"DELETE FROM Reaction WHERE idReact = {id};")
        self.cnx.commit()

    def deleteBG(self, idBG : int, target : int):
        if target == 0:
            self.cursor.execute(f"DELETE FROM BelongG WHERE idUser = {idBG};")
        elif target == 1:
            self.cursor.execute(f"DELETE FROM BelongG WHERE idGuild = {idBG};")
        self.cnx.commit()

    def deleteBC(self, id : int, target : int):
        if target == 0:
            self.cursor.execute(f"DELETE FROM BelongC WHERE idUser = {id};")
        elif target == 1:
            self.cursor.execute(f"DELETE FROM BelongC WHERE idChannel = {id};")
        self.cnx.commit()


    ###############
    ###############
    ############### Add
    ###############
    ###############


    def newUser(self, idUser : int, idGuild : int, year : int, doCommit : bool):
        add_user = "INSERT INTO User(idUser, yearDate) VALUES(%s, %s);"
        data_user = (idUser, year)
        add_belong = "INSERT INTO BelongG(idUser, idGuild, numberMsg, nbSecond) VALUES(¨%s, %s, 0, 0);"
        data_belong = (idUser, idGuild)

        self.cursor.execute(add_user, data_user)
        self.cursor.execute(add_belong, data_belong)
        
        if doCommit:
            self.cnx.commit()

    def addOneUser(self, idUser : int, idGuild : int, year : int):
        add_user = "INSERT INTO User(idUser, yearDate) VALUES (%s, %s);"
        data_user = (idUser, year)
        add_belong = "INSERT INTO BelongG(idUser, idGuild, numberMsg, nbSecond) VALUES(%s, %s, 0, 0);"
        data_belong = (idUser, idGuild)
        upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {idGuild};"

        self.cursor.execute(add_user, data_user)
        self.cursor.execute(add_belong, data_belong)
        self.cursor.execute(upd_guild)
        self.cnx.commit()

    def addGuild(self, idGuild : int, total = 0):
        add_guild = "INSERT INTO Guild(idGuild, totalMembers) VALUES(%s, %s);"
        data_guild = (idGuild, total)
        self.cursor.execute(add_guild, data_guild)

    def addChannel(self, idChan, idGuild, doCommit : bool):
        add_chan = "INSERT IGNORE Channel(idChannel, idGuild) VALUES(%s, %s);"
        data_chan = (idChan, idGuild)
        self.cursor.execute(add_chan, data_chan)

        if doCommit:
            self.cnx.commit()

    def addReact(self, idReact, idGuild, name, doCommit : bool):
        add_emoji = "INSERT INTO Reaction(idReact, idGuild, numberReact, nameReact) VALUES(%s, %s, %s, %s);"
        data_emoji = (idReact, idGuild, 0, name)
        self.cursor.execute(add_emoji, data_emoji)

        if doCommit:
            self.cnx.commit()

    def addBG(self, idUser : int, idGuild : int, doCommit : bool):
        add_BG = "INSERT INTO BelongG(idUser, idGuild) VALUES(%s, %s);"
        data_BG = (idUser, idGuild)
        self.cursor.execute(add_BG, data_BG)
        
        if doCommit:
            self.cnx.commit()

    def addBC(self, idUser : int, idChannel : int, doCommit : bool):
        add_BC = "INSERT INTO BelongC(idUser, idChannel) VALUES(%s, %s);"
        data_BC = (idUser, idChannel)
        self.cursor.execute(add_BC, data_BC)

        if doCommit:
            self.cnx.commit()
    
    ###############
    ###############
    ############### Index
    ###############
    ###############


    def getGuilds(self) -> list:
        select = f"""SELECT idGuild, chanStatID, newMembers, lostMembers, totalMembers, lastSend, keyWord, nbKeyWord, autoRefresh
                     FROM Guild
                     WHERE (sendStatus = '1' AND DATEDIFF(CAST(NOW() AS DATE), lastSend) >= 1)
                        OR (sendStatus = '2' AND DATEDIFF(CAST(NOW() AS DATE), lastSend) >= 7)
                        OR (sendStatus = '3' AND DATEDIFF(CAST(NOW() AS DATE), lastSend) >= 30);"""

        self.cursor.execute(select)
        return self.cursor.fetchall()

    def embedStat(self, guild : discord.Guild):
        self.cursor.execute(f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongG WHERE idGuild = {guild.id}) FROM BelongG WHERE idGuild = {guild.id} ORDER BY numberMsg DESC LIMIT 5;")
        queryM = self.cursor.fetchall()
        self.cursor.execute(f"SELECT idReact, nameReact, numberReact, (SELECT SUM(numberReact) FROM Reaction WHERE idGuild = {guild.id}) FROM reaction WHERE idGuild = {guild.id} ORDER BY numberReact DESC LIMIT 5;")
        queryR = self.cursor.fetchall()
        self.cursor.execute(f"SELECT idChannel, numberMsg FROM Channel WHERE idGuild = {guild.id} ORDER BY numberMsg DESC LIMIT 5;")
        queryC = self.cursor.fetchall()

        return queryM, queryR, queryC

    def updStat(self, guildID):
        upd_guild = f"UPDATE Guild SET newMembers = 0, lostMembers = 0, lastSend = CAST(NOW() AS DATE) WHERE idGuild = {guildID};"
        upd_belongG = f"UPDATE BelongG SET numberMsg = 0 WHERE idGuild = {guildID};"
        upd_chan = f"UPDATE Channel SET numberMsg = 0 WHERE idGuild = {guildID};"
        upd_react = f"UPDATE Reaction SET numberReact = 0 WHERE idGuild = {guildID};"

        self.cursor.execute(upd_guild)
        self.cursor.execute(upd_belongG)
        self.cursor.execute(upd_chan)
        self.cursor.execute(upd_react)


    ###############
    ###############
    ############### Admin
    ###############
    ###############


    def updKeyWord(self, word : str, id : int):
        upd_guild = f"UPDATE Guild SET keyWord = '{word}', nbKeyWord = 0 WHERE idGuild = {id};"
        self.cursor.execute(upd_guild)
        self.cnx.commit()

    def updCountKW(self, id : int, count : int = 0):
        upd_guild = f"UPDATE Guild SET nbKeyWord = nbKeyWord + {count} WHERE idGuild = {id};"
        self.cursor.execute(upd_guild)
        self.cnx.commit()

    def updAdd(self, value : str, id : int):
        self.cursor.execute(f"UPDATE Guild SET autoAdd = '{value}' WHERE idGuild = {id};")
        self.cnx.commit()

    def updRefresh(self, value : str, id : int):
        self.cursor.execute(f"UPDATE Guild SET autoRefresh = '{value}' WHERE idGuild = {id};")
        self.cnx.commit()     

    def updNewMembers(self, count : int, id : int):
        self.cursor.execute(f"UPDATE Guild SET newMembers = newMembers + {count}, totalMembers = totalMembers + {count} WHERE idGuild = {id};")
        self.cnx.commit()

    def resetChannel(self, idGuild : int, idChannel :int = None):
        if idChannel == None:
            upd = f"UPDATE Channel SET numberMsg = 0 WHERE idGuild = {idGuild};"
        else:
            upd = f"UPDATE Channel SET numberMsg = 0 WHERE idGuild = {idGuild} AND idChannel = {idChannel};"
        self.cursor.execute(upd)
        self.cnx.commit()

    def resetMsgChan(self, idChan):
        self.cursor.execute(f"UPDATE BelongC SET numberMsg = 0 WHERE idChannel = {idChan};")
        self.cnx.commit()

    def resetReact(self, idGuild):
        self.cursor.execute(f"UPDATE Reaction set numberReact = 0 WHERE idGuild = {idGuild};")
        self.cnx.commit()

    def resetGuild(self, idGuild):
        self.cursor.execute(f"UPDATE Guild SET newMembers = 0, lostMembers = 0, nbKeyWord = 0 WHERE idGuild = {idGuild};")
        self.cnx.commit()

    def setSend(self, idGuild, idChannel, status):
        self.cursor.execute(f"UPDATE Guild SET sendStatus = '{status}', chanStatID = {idChannel}, lastSend = CAST(NOW() AS DATE) WHERE idGuild = {idGuild};")
        self.cnx.commit()

    def unsetSend(self, idGuild):
        self.cursor.execute(f"UPDATE Guild SET chanStatID = NULL, sendStatus = '0' WHERE idGuild = {idGuild};")

    ###############
    ############### 
    ############### Events
    ###############
    ###############

    def addMsg(self, idUser : int, idGuild : int, idChannel : int):
        self.cursor.execute(f"UPDATE Channel SET numberMsg = numberMsg + 1 WHERE idChannel = {idChannel};")
        self.cursor.execute(f"UPDATE BelongG SET numberMsg = numberMsg + 1 WHERE idUser = {idUser} AND idGuild = {idGuild};")
        self.cursor.execute(f"UPDATE BelongC SET numberMsg = numberMsg + 1 WHERE idUser = {idUser} AND idChannel = {idChannel};")
        self.cnx.commit()

    def rmvMember(self, idUser : int, idGuild : int):
        self.cursor.execute(f"DELETE FROM BelongG WHERE idUser = {idUser} AND idGuild = {idGuild};")
        self.cursor.execute(f"DELETE FROM BelongC WHERE idUser = {idUser};")
        self.cursor.execute(f"UPDATE Guild SET lostMembers = lostMembers + 1, totalMembers = totalMembers - 1 WHERE idGuild = {idGuild};")
        self.cnx.commit()

    def newReact(self, idReact : int):
        self.cursor.execute(f"UPDATE Reaction SET numberReact = numberReact + 1 WHERE idReact = {idReact};")
        self.cnx.commit()

    def reactRemove(self, idReact : int, count : int):
        self.cursor.execute(f"UPDATE Reaction SET numberReact = numberReact - {count} WHERE idReact = {idReact};")
        self.cnx.commit()

    def newReactName(self, idReact : int, name : str):
        self.cursor.execute(f"UPDATE Reaction SET nameReact = '{name}' WHERE idReact = {idReact};")
        self.cnx.commit()

    def setJoinVoc(self, idUser : int):
        self.cursor.execute(f"UPDATE User SET joinVoc = NOW() WHERE idUser = {idUser};")
        self.cnx.commit()

    def resetJoin(self, idUser : int, idGuild : int, count : int):
        self.cursor.execute(f"UPDATE User SET joinVoc = NULL WHERE idUser = {idUser};")
        self.cursor.execute(f"UPDATE BelongG SET nbSecond = nbSecond + {count} WHERE idUser = {idUser} AND idGuild = {idGuild};")
        self.cnx.commit()


    ###############
    ###############
    ############### Usage
    ###############
    ###############


    def countUser(self) -> int:
        self.cursor.execute(f"SELECT COUNT(idUser) FROM User;")
        return self.cursor.fetchall()[0][0]

    def countGuild(self) -> int:
        self.cursor.execute(f"SELECT COUNT(idGuild) FROM Guild;")
        return self.cursor.fetchall()[0][0]

    def getYearCount(self, year : int, idGuild : int):
        self.cursor.execute(f"SELECT COUNT(yearDate) FROM BelongG bg INNER JOIN User u ON bg.idUser = u.idUser WHERE yearDate = {year} AND bg.idGuild = {idGuild};")
        return self.cursor.fetchall()

    def countUserGuild(self, idGuild : int) -> int:
        self.cursor.execute(f"SELECT COUNT(idUser) FROM BelongG WHERE idGuild = {idGuild};")
        return self.cursor.fetchall()[0][0]

    ###############
    ###############
    ############### Stats
    ###############
    ###############

    def getUsageChannel(self, idChan : int, limit : int):
        self.cursor.execute(f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongC WHERE idChannel = {idChan}) FROM BelongC WHERE idChannel = {idChan} ORDER BY numberMsg DESC LIMIT {limit};")
        select1 = self.cursor.fetchall()
        self.cursor.execute(f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongC WHERE idChannel = {idChan}) FROM BelongC WHERE idChannel = {idChan} ORDER BY numberMsg LIMIT {limit};")
        select2 = self.cursor.fetchall()
        return select1, select2

    def userMsg(self, idUser : int):
        self.cursor.execute(f"""SELECT COUNT(idGuild), SUM(bg.numberMsg)
                                FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                                WHERE u.idUser = {idUser}""")
        return self.cursor.fetchall()

    def userMsgChan(self, idUser : int, chanExist : bool, idChan : int = None):
        if chanExist:
            self.cursor.execute(f"""SELECT COUNT(idGuild), SUM(bg.numberMsg), bg.nbSecond, 0
                                    FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                                    WHERE u.idUser = {idUser};""")
        else:
            self.cursor.execute(f"""SELECT COUNT(idGuild), SUM(bg.numberMsg), bg.nbSecond, bc.numberMsg
                                    FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                                                INNER JOIN BelongC bc ON u.idUser = bc.idUser
                                    WHERE u.idUser = {idUser} AND bc.idChannel = {idChan};""")
        return self.cursor.fetchall()

    def topMessages(self, limit : int):
        self.cursor.execute(f"SELECT idUser, SUM(numberMsg) FROM BelongG GROUP BY idUser ORDER BY numberMsg DESC LIMIT {limit};")
        return self.cursor.fetchall()

    def topVoiceChat(self, limit : int):
        self.cursor.execute(f"SELECT idUser, SUM(nbSecond) FROM BelongG GROUP BY idUser ORDER BY nbSecond DESC LIMIT {limit};")
        return self.cursor.fetchall()

    def activity(self, idUser : int, idGuild : int):
        self.cursor.execute(f"""SELECT bc.idChannel, bc.numberMsg
                                FROM Channel c INNER JOIN BelongC bc ON c.idChannel = bc.idChannel
                                WHERE c.idGuild = {idGuild} AND bc.idUser = {idUser};""")
        return self.cursor.fetchall()

    ###############
    ###############
    ############### 
    ###############
    ###############