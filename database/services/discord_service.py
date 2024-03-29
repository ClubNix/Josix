from database.database import DatabaseHandler
from database.db_utils import (
    GuildDB,
    LinkUserGuild,
    UserDB,
    error_handler,
)


@error_handler
def get_guild(handler: DatabaseHandler, id_guild: int) -> GuildDB | None:
    query = "SELECT * FROM josix.Guild WHERE idGuild = %s;"
    handler.cursor.execute(query, (id_guild,))
    res = handler.cursor.fetchone()

    if res:
        return GuildDB(*res)
    return None


@error_handler
def get_user(handler: DatabaseHandler, id_user: int) -> UserDB | None:
    query = "SELECT * FROM josix.User WHERE idUser = %s;"
    handler.cursor.execute(query, (id_user,))
    res = handler.cursor.fetchone()

    if res:
        return UserDB(*res)
    return None


@error_handler
def get_user_in_guild(handler: DatabaseHandler, id_user: int, id_guild: int) -> LinkUserGuild | None:
    query = """SELECT * FROM josix.UserGuild
                WHERE idUser = %s AND idGuild  = %s;"""
    params = (id_user, id_guild)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()

    if res:
        return LinkUserGuild(*res)
    return None


def get_link_user_guild(handler: DatabaseHandler, id_user: int, id_guild: int) -> tuple[UserDB | None, GuildDB | None, LinkUserGuild | None]:
    return (
        get_user(handler, id_user),
        get_guild(handler, id_guild),
        get_user_in_guild(handler, id_user, id_guild)
    )


@error_handler
def add_guild(handler: DatabaseHandler, id_guild: int, id_chan_stat: int = 0, id_chan_xp: int = 0) -> None:
    query = """INSERT INTO josix.Guild(idGuild, chanNews, xpNews)
                VALUES (%s, %s, %s)"""
    params = (id_guild, id_chan_stat, id_chan_xp)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def add_user(handler: DatabaseHandler, id_user: int) -> None:
    query = "INSERT INTO josix.User (idUser) VALUES (%s);"
    handler.cursor.execute(query, (id_user,))
    handler.conn.commit()


@error_handler
def add_user_in_guild(handler: DatabaseHandler, id_user: int, id_guild: int) -> None:
    query = "INSERT INTO josix.UserGuild(idUser, idGuild) VALUES (%s, %s);"
    params = (id_user, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def fetch_user_guild_relationship(handler: DatabaseHandler, id_user: int, id_guild: int) -> tuple[UserDB | None, GuildDB | None, LinkUserGuild | None]:
    """
    Fetch data the same way as `get_link_user_guild` but creates and returns data if its missing
    """
    userDB, guildDB, userGuildDB = get_link_user_guild(handler, id_user, id_guild)

    if not userDB:
        add_user(handler, id_user)
        userDB = get_user(handler, id_user)
    if not guildDB:
        add_guild(handler, id_guild)
        guildDB = get_guild(handler, id_guild)
    if not userGuildDB:
        add_user_in_guild(handler, id_user, id_guild)
        userGuildDB = get_user_in_guild(handler, id_user, id_guild)
    return userDB, guildDB, userGuildDB