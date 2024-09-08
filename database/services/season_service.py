from datetime import datetime

from database.database import DatabaseHandler
from database.db_utils import (
    GuildDB,
    Score,
    Season,
    UserScore,
    error_handler,
)
from database.services.discord_service import get_link_user_guild
from database.services.guild_service import start_temporary_season
from database.services.xp_service import clean_xp_guild_soft, get_leaderboard


@error_handler
def get_season_by_label(handler: DatabaseHandler, id_guild: int, label: str) -> Season | None:
    query = "SELECT * FROM josix.Season WHERE idGuild = %s AND LOWER(label) = LOWER(%s);"
    params = (id_guild, label)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()
    if res:
        return Season(*res)
    return None


@error_handler
def get_new_season_id(handler: DatabaseHandler, id_guild: int) -> int:
    query = "SELECT COUNT(idSeason) FROM josix.Season WHERE idGuild = %s;"
    handler.cursor.execute(query, (id_guild,))
    res = handler.cursor.fetchone()
    newLabelID = 1 if not res else res[0]+1

    if get_season_by_label(handler, id_guild, str(newLabelID)):
        raise ValueError(f"The label '{newLabelID}' is already used in a season for this server")
    return newLabelID


@error_handler
def get_season(handler: DatabaseHandler, id_season: int) -> Season | None:
    query = "SELECT * FROM josix.Season WHERE idSeason = %s;"
    handler.cursor.execute(query, (id_season,))
    res = handler.cursor.fetchone()
    if res:
        return Season(*res)
    return None


@error_handler
def get_seasons(handler: DatabaseHandler, id_guild: int, limit: int) -> list[Season] | None:
    query = "SELECT * FROM josix.Season WHERE idGuild = %s ORDER BY idSeason DESC LIMIT %s;"
    params = (id_guild, limit)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchall()

    if res:
        return [Season(*row) for row in res]
    return None


@error_handler
def get_user_history(handler: DatabaseHandler, id_guild: int, id_user: int) -> list[UserScore] | None:
    query = """
            SELECT sc.idUser, sc.idSeason, sc.score, sc.ranking, se.label
            FROM josix.Score sc INNER JOIN josix.Season se ON sc.idSeason = se.idSeason
            WHERE sc.idUser = %s AND se.idGuild = %s ORDER BY sc.idSeason DESC;
            """
    params = (id_user, id_guild)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchall()

    if res:
        return [UserScore(*score) for score in res]
    return None


@error_handler
def get_scores(handler: DatabaseHandler, id_season: int) -> list[Score] | None:
    query = """SELECT * FROM josix.Score WHERE idSeason = %s ORDER BY ranking;"""
    handler.cursor.execute(query, (id_season,))
    res = handler.cursor.fetchall()
    
    if res:
        return [Score(*score) for score in res]
    return None


@error_handler
def get_user_score(handler: DatabaseHandler, id_season: int, id_user: int) -> Score | None:
    query = "SELECT * FROM josix.Score WHERE idSeason = %s AND idUser = %s;"
    params = (id_season, id_user)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()

    if res:
        return Score(*res)
    return None


@error_handler
def store_season(handler: DatabaseHandler, id_guild: int, label: str | None, temporary: bool = False) -> int | None:
    if not label:
        label = str(get_new_season_id(handler, id_guild))
    else:
        if get_season_by_label(handler, id_guild, str(label)):
            raise ValueError(f"The label '{label}' is already used in a season for this server")

    query = "INSERT INTO josix.Season(idGuild, label, temporary) VALUES(%s, LOWER(%s), %s) RETURNING idSeason;"
    params = (id_guild, label, temporary)
    handler.cursor.execute(query, params)
    handler.conn.commit()
    
    res = handler.cursor.fetchone()
    if res:
        return res[0]
    return None


@error_handler
def store_scores(handler: DatabaseHandler, id_guild: int, id_season: int, temporary: bool = False) -> None:
    scores = get_leaderboard(handler, id_guild, None)
    if not scores:
        return

    for i, score in enumerate(scores):
        query = "INSERT INTO josix.Score VALUES(%s, %s, %s, %s);"
        params = (score.idUser, id_season, score.xp, i+1)
        handler.cursor.execute(query, params)
    handler.conn.commit()

    if temporary:
        query = "UPDATE josix.Season SET ended_at = NOW() WHERE idSeason = %s;"
        handler.cursor.execute(query, (id_season,))
        handler.conn.commit()


@error_handler
def update_season_label(handler: DatabaseHandler, season: Season, new_label: str) -> None:
    query = "UPDATE josix.Season SET label = %s WHERE idSeason = %s;"
    params = (new_label, season.idSeason)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def delete_season(handler: DatabaseHandler, season: Season) -> None:
    query = "DELETE FROM josix.Score sc USING josix.Season se WHERE sc.idSeason = se.idSeason AND sc.idSeason = %s AND se.idGuild = %s;"
    query2 = "DELETE FROM josix.Season WHERE idSeason = %s AND idGuild = %s;"
    params = (season.idSeason, season.idGuild)
    handler.cursor.execute(query, params)
    handler.cursor.execute(query2, params)
    handler.conn.commit()


@error_handler
def rebase_scores(handler: DatabaseHandler, season: Season) -> None:
    id_season, id_guild = season.idSeason, season.idGuild
    scores = get_scores(handler, id_season)
    if not scores:
        return

    for _, score in enumerate(scores):
        if get_link_user_guild(handler, score.idUser, id_guild):
            query = "UPDATE josix.UserGuild SET xp = %s WHERE idUser = %s AND idGuild = %s;"
            params = (score.score, score.idUser, id_guild)
            handler.cursor.execute(query, params)
        else:
            query = "INSERT INTO josix.UserGuild(idUser, idGuild, xp) VALUES(%s, %s, %s);"
            params = (score.idUser, id_guild, score.score)
            handler.cursor.execute(query)
    handler.conn.commit()
    delete_season(handler, season)

@error_handler
def get_last_season(handler: DatabaseHandler, id_guild: int, temporary: bool) -> Season | None:
    query = "SELECT * FROM josix.Season WHERE idGuild = %s AND temporary = %s ORDER BY ended_at DESC LIMIT 1;"
    params = (id_guild, temporary)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()
    if res:
        return Season(*res)
    return None


@error_handler
def create_temp_season(handler: DatabaseHandler, id_guild: int, label: str, end: datetime):
    store_season(handler, id_guild, label, True)
    stored_id = store_season(handler, id_guild, "", False)
    store_scores(handler, id_guild, stored_id)
    start_temporary_season(handler, id_guild, end)
    clean_xp_guild_soft(handler, id_guild)


@error_handler
def stop_temporary_season(handler: DatabaseHandler, id_guild: int):
    last_temp = get_last_season(handler, id_guild, True)
    last = get_last_season(handler, id_guild, False)
    if not last_temp:
        raise ValueError("No temporary season is active")

    store_scores(handler, id_guild, last_temp.idSeason, True)
    if last:
        rebase_scores(handler, last)

    query = "UPDATE josix.Guild SET tempSeasonActive = FALSE WHERE idGuild = %s;"
    handler.cursor.execute(query, (id_guild,))
    handler.conn.commit()


@error_handler
def get_guilds_ended_temporary(handler: DatabaseHandler) -> list[GuildDB] | None:
    query = "SELECT * FROM josix.Guild WHERE tempSeasonActive = TRUE AND endTempSeason <= %s;"
    handler.cursor.execute(query, (datetime.now(),))
    res = handler.cursor.fetchall()
    if res:
        return [GuildDB(*row) for row in res]
    return None