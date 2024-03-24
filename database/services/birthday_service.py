from database.database import DatabaseHandler
from database.db_utils import (
    Birthday,
    BirthdayAuto,
    error_handler,
)


@error_handler
def check_birthday(handler: DatabaseHandler, day: int, month: int) -> list[BirthdayAuto] | None:
    query = """SELECT u.idUser AS "user", ug.idGuild as "guild",
                        EXTRACT(DAY FROM u.hbDate) AS "day",
                        EXTRACT(MONTH FROM u.hbDate) AS "month"
                FROM josix.User u INNER JOIN josix.UserGuild ug ON u.idUser = ug.idUser
                WHERE EXTRACT(YEAR FROM u.hbDate) < EXTRACT(YEAR FROM NOW()) AND
                        EXTRACT(DAY FROM u.hbDate) = %s AND
                        EXTRACT(MONTH FROM u.hbDate) = %s;"""
    params = (day, month)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchall()
    if res:
        return [BirthdayAuto(*row) for row in res]
    return None


@error_handler
def get_birthday_month(handler: DatabaseHandler, id_guild: int, month: int) -> list[Birthday] | None:
    query = """SELECT u.idUser, EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate)
                FROM josix.User u INNER JOIN josix.UserGuild ug ON u.idUser = ug.idUser
                WHERE ug.idGuild = %s AND EXTRACT(MONTH FROM u.hbDate) = %s
                ORDER BY EXTRACT(DAY FROM u.hbDate), EXTRACT(MONTH FROM u.hbDate);"""
    handler.cursor.execute(query, (id_guild, month))
    res = handler.cursor.fetchall()
    if res:
        return [Birthday(*row) for row in res]
    return None


@error_handler
def update_user_birthday(handler: DatabaseHandler, id_user: int, day: int, month: int, year: int) -> None:
    newBd = f"'{year}-{month}-{day}'"
    query = """UPDATE josix.User
                SET hbDate = %s
                WHERE idUser = %s;"""
    params = (newBd, id_user)
    handler.cursor.execute(query, params)
    handler.conn.commit()


@error_handler
def remove_user_birthday(handler: DatabaseHandler, id_user: int) -> None:
    query = """UPDATE josix.User
                SET hbDate = NULL
                WHERE idUser = %s;"""
    handler.cursor.execute(query, (id_user,))
    handler.conn.commit() 
