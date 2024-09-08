from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable

import psycopg2

from database.database import DatabaseHandler
from pkg.bot_utils import JosixDatabaseException

# TODO : add dataclasses param checking on start (same name/order)

def error_handler(func: Callable):
    def wrapper(*args):
        if not args or not isinstance(args[0], DatabaseHandler):
            raise JosixDatabaseException("The service must have at least one argument from the type DatabaseHandler")

        try:
            return func(*args)
        except psycopg2.Error as dbError:
            args[0].conn.rollback()
            raise dbError
        except Exception as commonError:
            raise commonError
    return wrapper


@dataclass()
class UserDB:
    """Dataclass that represents a User in the database"""
    id: int
    elo: int
    nbGames: int
    hbDate: date

@dataclass()
class GuildDB:
    """Dataclass that represents a Guild in the database"""
    id: int
    chanNews: int
    xpNews: int
    enableXp: bool
    enableWelcome: bool
    wChan: int
    wRole: int
    wText: str
    logNews: int
    blockedCat: list[int]
    tempSeasonActive: bool
    endTempSeason: datetime

@dataclass()
class LinkUserGuild:
    """Dataclass that represents a link between a User and a Guild in the database"""
    idUser: int
    idGuild: int
    xp: int
    lvl: int
    lastMessage: datetime
    isUserBlocked: bool

@dataclass()
class MsgReact:
    """Dataclass that represents a Reaction Message of a guild in the database"""
    id: int
    idGuild: int

@dataclass()
class ReactCouple:
    """Dataclass that represents a Reaction couple of emoji and role in the database"""
    id: int
    emoji: str
    idRole: int

@dataclass()
class LogSelection:
    """Dataclass that represents a Log Selection of a guild in the database"""
    idGuild: int
    logs: list[int]

@dataclass()
class GameType:
    """Dataclass that represents a Type of Game in the database"""
    id: int
    name: str
    
@dataclass()
class Game:
    """Dataclass that represents a Game in the database"""
    id: int
    idType: int
    idUser: int
    opponent: int

@dataclass()
class BirthdayAuto:
    """Dataclass that represents data retrieved from the database for automatic birthday reminder"""
    idUser: int
    idGuild: int
    day: int
    month: int

@dataclass()
class Birthday:
    """Dataclass that represent the birthday of a user"""
    idUser: int
    day: int
    month: int

@dataclass()
class Season:
    """Dataclass that represents a XP season"""
    idSeason: int
    idGuild: int
    label: str
    ended_at: datetime
    temporary: bool

@dataclass()
class UserScore:
    """Dataclass that represents a score obtained for a user in a season"""
    idUser: int
    idSeason: int
    score: int
    ranking: int
    label: str

@dataclass()
class Score:
    """Dataclass that represents a simple score"""
    idUser: int
    idSeason: int
    score: int
    ranking: int