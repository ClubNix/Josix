import discord

from database.database import DatabaseHandler
from database.db_utils import Game, GameType, error_handler


@error_handler
def get_game_from_user(handler: DatabaseHandler, id_user: int) -> Game | None:
    query = "SELECT * FROM josix.Games WHERE idUser = %s OR opponent = %s;"
    handler.cursor.execute(query, (id_user, id_user))
    res = handler.cursor.fetchone()

    if res:
        return Game(*res)
    return None


@error_handler
def get_game_type(handler: DatabaseHandler, game_name: str) -> GameType | None:
    query = "SELECT * FROM josix.GameType WHERE gameName = %s;"
    handler.cursor.execute(query, (game_name,))
    res = handler.cursor.fetchone()

    if res:
        return GameType(*res)
    return None


@error_handler
def get_existing_game(handler: DatabaseHandler, id_game: int, id_user: int) -> Game | None:
    """May seems weird but its to ensure a player is in this specific game"""
    query = """SELECT * FROM josix.Games
                WHERE idGame = %s AND (idUser = %s OR opponent = %s);"""
    params = (id_game, id_user, id_user)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()

    if res:
        return Game(*res)
    return None


@error_handler
def add_game_type(handler: DatabaseHandler, game_name: str) -> None:
    query = "INSERT INTO josix.GameType(gameName) VALUES(%s);"
    handler.cursor.execute(query, (game_name,))
    handler.conn.commit()


@error_handler
def add_game(handler: DatabaseHandler, game_name: str, id_user: int, opponent: int | None = None) -> int | None:
    game_type = get_game_type(handler, game_name).id
    if not game_type:
        return None
    
    typeId = game_type
    query = "INSERT INTO josix.Games(idType, idUser, opponent) VALUES(%s, %s, %s) RETURNING idGame;"
    params = (typeId, id_user, opponent)
    handler.cursor.execute(query, params)
    handler.conn.commit()

    res = handler.cursor.fetchone()
    if res:
        return res[0]
    return None


@error_handler
def quit_game(handler: DatabaseHandler, id_user: int) -> None:
    query = "DELETE FROM josix.Games WHERE idUser = %s OR opponent = %s;"
    handler.cursor.execute(query, (id_user, id_user))
    handler.conn.commit()


@error_handler
def delete_single_game(handler: DatabaseHandler, gameId: int) -> None:
    query = "DELETE FROM josix.Games WHERE idGame = %s;"
    handler.cursor.execute(query, (gameId,))
    handler.conn.commit()


@error_handler
def delete_games(handler: DatabaseHandler) -> None:
    query = "DELETE FROM josix.Games;"
    handler.cursor.execute(query)
    handler.conn.commit()


###
###

# old dart system. Not updated

@error_handler
def getPlayerStat(handler: DatabaseHandler, id_user: int) -> tuple[int, int] | None:
    query = "SELECT elo, nbGames FROM josix.User WHERE idUser = %s;"
    handler.cursor.execute(query, (id_user,))
    res = handler.cursor.fetchone()
    if not res:
        return None
    return res # type: ignore


@error_handler
def addDartLog(handler: DatabaseHandler, id_guild: int, winner: discord.User, foes: tuple[discord.User]) -> None:
    text = ""
    for foe in foes:
        text += foe.name + "', '"
    text = text[0:len(text)-3]

    query = """INSERT INTO josix.DartLog (idGuild, winnerName, losersName)
                VALUES (%s, %s, ARRAY[%s])"""
    params = (id_guild, winner.name, text)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def updatePlayerStat(handler: DatabaseHandler, id_user: int, new_elo: int) -> None:
    query = """UPDATE josix.User
                SET elo = %s, nbGames = nbGames + 1
                WHERE idUser = %s;"""
    params = (new_elo, id_user)
    handler.cursor.execute(query, params)
    handler.conn.commit()