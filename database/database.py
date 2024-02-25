import datetime as dt
import os
from shutil import copyfile
from typing import Any, Callable

import psycopg2
from dotenv import load_dotenv

import logwrite as log

SCRIPT_DIR = os.path.dirname(__file__)
BACKUP_PATH = os.path.join(SCRIPT_DIR, 'backup.sql')
DAILY_BACKUP_PATH = os.path.join(SCRIPT_DIR, 'daily_backup.sql')
OLD_PATH = os.path.join(SCRIPT_DIR, 'daily_backup.sql.old')
TABLE_ORDER_PATH = os.path.join(SCRIPT_DIR, 'table_order.sql')

class DatabaseHandler():
    """
    Represents an handler for the database.
    Allows to execute queries on the database
    """
    def __init__(self) -> None:
        load_dotenv(".env.dev")

        conn = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        log.writeLog(" - Connection on the database for Josix done")

        self.conn = conn
        self.cursor = conn.cursor()

    # TODO : Use it in another way
    def safeExecute(
        self,
        func: Callable[[Any], Any],
        *args
        ) -> Any:
        try:
            return func(*args)
        except Exception as e:
            log.writeError(log.formatError(e))


    def _error_handler(func: Callable):
        def wrapper(ref, *args):
            try:
                return func(ref, *args)
            except psycopg2.Error as dbError:
                ref: DatabaseHandler = ref
                ref.conn.rollback()
                raise dbError
            except Exception as commonError:
                raise commonError
        return wrapper


    def execute(self, query: str, raiseError: bool = False) -> str:
        if query.startswith("--") or query.startswith("\n") or len(query) == 0:
            return "Empty query"

        try:
            self.cursor.execute(query)
            self.conn.commit()

            try:
                return str(self.cursor.fetchall())
            except psycopg2.ProgrammingError as prgError:
                if raiseError:
                    raise prgError
                return "Query executed : nothing to fetch"

        except psycopg2.Error as commonError:
            self.conn.rollback()
            if raiseError:
                raise commonError
            return str(commonError)


    @_error_handler
    def backup(self, table: str, daily: bool = False) -> None:
        if table:
            query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = 'josix' AND table_name = '{table}';"
        else:
            with open(TABLE_ORDER_PATH, 'r') as order_file:
                query = order_file.read()

        self.cursor.execute(query)
        res = self.cursor.fetchall()

        file = DAILY_BACKUP_PATH if daily else BACKUP_PATH
        if daily:
            copyfile(DAILY_BACKUP_PATH, OLD_PATH)

        with open(file, "w") as f:
            f.write("-- Last backup : " + str(dt.datetime.now()) + "\n")
            for rowTable in res[::-1]:
                f.write("DELETE FROM josix." + rowTable[0] + ";\n")
            for rowTable in res:
                table_name = rowTable[0]
                f.write("\n-- Records for table : josix." + table_name + "\n")

                self.cursor.execute("SELECT * FROM josix.%s" % (table_name))
                column_names = []
                columns_descr = self.cursor.description

                for c in columns_descr:
                    column_names.append(c[0])
                insert_prefix = 'INSERT INTO josix.%s (%s) VALUES ' % (table_name, ', '.join(column_names))
                rows = self.cursor.fetchall()

                for row in rows:
                    row_data = []
                    for rd in row:
                        if rd is None:
                            row_data.append('NULL')
                        elif isinstance(rd, dt.date):
                            row_data.append("'%s'" % (rd.strftime('%Y-%m-%d')))
                        elif isinstance(rd, dt.datetime):
                            row_data.append("'%s'" % (rd.strftime('%Y-%m-%d %H:%M:%S')))
                        elif isinstance(rd, str):
                            row_data.append("E'%s'" % (rd.replace("'", "\\'")))
                        elif isinstance(rd, list):
                            row_data.append("ARRAY%s::BIGINT[]" % (repr(rd)))
                        else:
                            row_data.append(repr(rd))
                    f.write('%s (%s);\n' % (insert_prefix, ', '.join(row_data)))