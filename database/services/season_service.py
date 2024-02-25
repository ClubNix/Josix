from database.database import DatabaseHandler
from database.db_utils import (
    error_handler,
    Score,
    UserScore,
    Season,
)
from database.services.xp_service import get_leaderboard


@error_handler
def get_season_by_label(handler: DatabaseHandler, id_guild: int, label: str) -> Season | None:
    query = "SELECT * FROM josix.Season WHERE idGuild = %s AND LOWER(label) = LOWER(%s);"
    params = (id_guild, label)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()
    if res:
        return Season(*res)


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


@error_handler
def get_seasons(handler: DatabaseHandler, id_guild: int, limit: int) -> list[Season] | None:
    query = "SELECT * FROM josix.Season WHERE idGuild = %s ORDER BY idSeason DESC LIMIT %s;"
    params = (id_guild, limit)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchall()

    if res:
        return [Season(*row) for row in res]


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


@error_handler
def get_scores(handler: DatabaseHandler, id_season: int) -> list[Score] | None:
    query = """SELECT * FROM josix.Score WHERE idSeason = %s ORDER BY ranking;"""
    handler.cursor.execute(query, (id_season,))
    res = handler.cursor.fetchall()
    
    if res:
        return [Score(*score) for score in res]


@error_handler
def get_user_score(handler: DatabaseHandler, id_season: int, id_user: int) -> Score | None:
    query = "SELECT * FROM josix.Score WHERE idSeason = %s AND idUser = %s;"
    params = (id_season, id_user)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()

    if res:
        return Score(*res)


@error_handler
def store_season(handler: DatabaseHandler, id_guild: int, label: str) -> int:
    if label == "":
        label = str(get_new_season_id(handler, id_guild))
    else:
        if get_season_by_label(handler, id_guild, str(label)):
            raise ValueError(f"The label '{label}' is already used in a season for this server")

    query = "INSERT INTO josix.Season(idGuild, label) VALUES(%s, LOWER(%s)) RETURNING idSeason;"
    params = (id_guild, label)
    handler.cursor.execute(query, params)
    handler.conn.commit()
    
    res = handler.cursor.fetchone()
    if res:
        return res[0]


@error_handler
def store_scores(handler: DatabaseHandler, id_guild: int, id_season: int):
    scores = get_leaderboard(handler, id_guild, None)
    if not scores:
        return
    
    season = get_season(handler, id_season)
    if not season:
        return

    for i, score in enumerate(scores):
        query = "INSERT INTO josix.Score VALUES(%s, %s, %s, %s);"
        params = (score.idUser, season.idSeason, score.xp, i+1)
        handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def update_season_label(handler: DatabaseHandler, season: Season, new_label: str) -> None:
    query = "UPDATE josix.Season SET label = %s WHERE idSeason = %s;"
    params = (new_label, season.idSeason)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def delete_season(handler: DatabaseHandler, season: Season) -> None:
    query = "DELETE FROM josix.Score WHERE idSeason = %s;"
    query2 = "DELETE FROM josix.Season WHERE idSeason = %s;"
    handler.cursor.execute(query, (season.idSeason,))
    handler.cursor.execute(query2, (season.idSeason,))
    handler.conn.commit()
