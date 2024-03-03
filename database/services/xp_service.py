import datetime as dt

from database.database import DatabaseHandler
from database.db_utils import LinkUserGuild, error_handler


@error_handler
def get_leaderboard(handler: DatabaseHandler, id_guild: int, limit: int | None) -> list[LinkUserGuild] | None:
    query = """SELECT * FROM josix.UserGuild
                WHERE idGuild = %s
                ORDER BY xp DESC
                LIMIT %s"""
    params = (id_guild, limit)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchall()
    if res:
        return [LinkUserGuild(*row) for row in res]
    return None


@error_handler
def get_ranking(handler: DatabaseHandler, id_user: int, id_guild: int) -> int | None:
    query = """SELECT COUNT(DISTINCT idUser) + 1
                FROM josix.UserGuild
                WHERE idGuild = %s AND
                      xp > (SELECT xp FROM josix.UserGuild WHERE idUser = %s AND idGuild = %s);"""
    params = (id_guild, id_user, id_guild)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()
    if res:
        return res[0]
    return None


@error_handler
def update_user_xp(handler: DatabaseHandler, id_user: int, id_guild: int, lvl: int, xp: int, last_send: dt.datetime) -> None:
    query = """UPDATE josix.UserGuild
                SET lvl = %s,
                    xp = %s,
                    lastMessage = %s
                WHERE idUser = %s AND idGuild = %s;"""
    params = (lvl, xp, last_send, id_user, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def change_channel_xp(handler: DatabaseHandler, id_guild: int, id_chan: int) -> None:
    query = """UPDATE josix.Guild
                SET xpNews = %s
                WHERE idGuild = %s;"""
    params = (id_chan, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def switch_xp_enabling(handler: DatabaseHandler, id_guild: int) -> None:
    query = """UPDATE josix.Guild
                SET enableXP = NOT enableXP
                WHERE idGuild = %s"""
    handler.cursor.execute(query, (id_guild,))
    handler.conn.commit()


@error_handler
def switch_user_xp_blocking(handler: DatabaseHandler, id_user: int, id_guild: int) -> None:
    query = """UPDATE josix.UserGuild
                SET xpBlocked = NOT xpBlocked
                WHERE idUser = %s AND idGuild = %s;"""
    params = (id_user, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def block_category_xp(handler: DatabaseHandler, id_category: int, id_guild: int) -> None:
    query = """UPDATE josix.Guild
                SET blockedCategories = ARRAY_APPEND(blockedCategories, %s)
                WHERE idGuild = %s;"""
    params = (id_category, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def unblock_category_xp(handler: DatabaseHandler, id_category: int, id_guild: int) -> None:
    query = """UPDATE josix.Guild
                SET blockedCategories = ARRAY_REMOVE(blockedCategories, %s)
                WHERE idGuild = %s;"""
    params = (id_category, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def clean_xp_guild(handler: DatabaseHandler, id_guild: int) -> None:
    query = "DELETE FROM josix.UserGuild WHERE idGuild = %s;"
    handler.cursor.execute(query, (id_guild,))
    handler.conn.commit()
