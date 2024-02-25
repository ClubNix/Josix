from database.database import DatabaseHandler
from database.db_utils import error_handler, LogSelection


@error_handler
def get_logs_selection(handler: DatabaseHandler, id_guild: int) -> LogSelection | None:
    query = "SELECT * FROM josix.LogSelector WHERE idGuild = %s ORDER BY idLog;"
    handler.cursor.execute(query, (id_guild,))
    res = handler.cursor.fetchall()

    if res:
        logs = []
        for row in res:
            logs.append(row[1])
        return LogSelection(id_guild, logs)


@error_handler
def update_logs_selection(handler: DatabaseHandler, id_guild: int, logs: list[int]) -> None:
    for i in range(1, 13):
        params = (id_guild, i)

        if i in logs:
            query = "INSERT INTO josix.LogSelector VALUES(%s, %s) ON CONFLICT DO NOTHING;"
        else:
            query = "DELETE FROM josix.LogSelector WHERE idGuild = %s AND idLog = %s;"
        handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def update_logs_entries(handler: DatabaseHandler, logs: list[tuple[str, int]]) -> None:
    for log_var in logs:
        query = "INSERT INTO josix.Logs VALUES(%s, %s) ON CONFLICT DO NOTHING;"
        params = (log_var[1], log_var[0])
        handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def update_log_channel(handler: DatabaseHandler, id_guild: int, id_chan: int | None) -> None:
    query = "UPDATE josix.Guild SET logNews = %s WHERE idGuild = %s;"
    params = (id_chan, id_guild)
    handler.cursor.execute(query, params)
    handler.conn.commit()
