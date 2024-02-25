from database.database import DatabaseHandler
from bot_utils import error_handler


@error_handler
def get_news_chan_from_user(handler: DatabaseHandler, id_user: int) -> list[int] | None:
    query = """SELECT chanNews 
                FROM josix.Guild g INNER JOIN josix.UserGuild ug ON g.idGuild = ug.idGuild
                WHERE idUser = %s AND chanNews IS NOT NULL;"""
    handler.cursor.execute(query, (id_user,))
    res = handler.cursor.fetchall()
    if res:
        return [row[0] for row in res]


@error_handler
def update_news_channel(handler: DatabaseHandler, id_guild: int, id_chan: int) -> None:
    query = """UPDATE josix.Guild
                SET chanNews = %s
                WHERE idGuild = %s;"""
    params = (id_chan, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()