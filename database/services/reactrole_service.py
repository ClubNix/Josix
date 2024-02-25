from database.database import DatabaseHandler
from database.db_utils import MsgReact, ReactCouple
from bot_utils import error_handler


@error_handler
def get_reaction_message(handler: DatabaseHandler, id_msg: int) -> MsgReact | None:
    query = "SELECT * FROM josix.Msgreact WHERE idMsg = %s;"
    handler.cursor.execute(query, (id_msg,))
    res = handler.cursor.fetchone()

    if res:
        return MsgReact(*res)


@error_handler
def get_role_from_reaction(handler: DatabaseHandler, id_msg: int, emoji_name: str) -> int | None:
    query = """SELECT idRole FROM josix.ReactCouple rc
                INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                WHERE mc.idMsg = %s AND rc.emoji = %s;"""
    params = (id_msg, emoji_name)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchone()
    if res:
        return res[0]


@error_handler
def get_couples(handler: DatabaseHandler, id_msg: int = None) -> list[ReactCouple] | None:
    if not id_msg:
        query = """SELECT rc.idCouple, rc.emoji, rc.idRole FROM josix.ReactCouple rc
                    INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple;"""
        params = ()
    else:
        query = """SELECT rc.idCouple, rc.emoji, rc.idRole FROM josix.ReactCouple rc
                    INNER JOIN josix.MsgCouple mc ON rc.idCouple = mc.idCouple
                    WHERE mc.idMsg = %s;"""
        params = (id_msg,)
    handler.cursor.execute(query, params)
    handler.cursor.execute(query, params)
    res = handler.cursor.fetchall()
    if res:
        return [ReactCouple(*row) for row in res]


@error_handler
def get_couple_from_role(handler: DatabaseHandler, id_role: int) -> list[ReactCouple] | None:
    query = "SELECT * FROM josix.ReactCouple WHERE idRole = %s;"
    handler.cursor.execute(query, (id_role,))
    res = handler.cursor.fetchone()
    if res:
        return [ReactCouple(*row) for row in res]


@error_handler
def add_couple(handler: DatabaseHandler, couple: tuple, id_msg: int) -> None:
    if len(couple) != 2:
        return
        
    query1 = """INSERT INTO josix.ReactCouple (emoji, idRole)
                VALUES (%s, %s) RETURNING idCouple;"""
    params = (couple[0], couple[1])
    handler.cursor.execute(query1, params)
    idCouple = handler.cursor.fetchone()[0]

    query2 = "INSERT INTO josix.MsgCouple VALUES (%s,%s);"
    params = (id_msg, idCouple)
    handler.cursor.execute(query2, params)
    handler.conn.commit()


@error_handler
def delete_message_react(handler: DatabaseHandler, id_msg: int) -> None:
    query = "DELETE FROM josix.MsgCouple WHERE idMsg = %s;"
    query2 = "DELETE FROM josix.MsgReact WHERE idMsg = %s;"
    handler.cursor.execute(query, (id_msg,))
    handler.cursor.execute(query2, (id_msg,))
    handler.conn.commit()


@error_handler
def delete_reaction_couple(handler: DatabaseHandler, id_couple: int) -> None:
    query = "DELETE FROM josix.MsgCouple WHERE idCouple = %s;"
    query2 = "DELETE FROM josix.ReactCouple WHERE idCouple = %s;"
    handler.cursor.execute(query, (id_couple,))
    handler.cursor.execute(query2, (id_couple,))
    handler.conn.commit()


@error_handler
def delete_message_couple(handler: DatabaseHandler, id_msg: int, id_couple: int) -> None:
    query = "DELETE FROM josix.MsgCouple WHERE idMsg = %s AND idCouple = %s;"
    params = (id_msg, id_couple)
    handler.cursor.execute(query, params)
    handler.conn.commit()