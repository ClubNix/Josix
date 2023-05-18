from dataclasses import dataclass
from datetime import datetime, date

@dataclass()
class UserDB:
    id: int
    elo: int
    nbGames: int
    hbDate: date

@dataclass()
class GuildDB:
    id: int
    chanNews: int
    xpNews: int
    enableXp: bool

@dataclass()
class LinkUserGuild:
    idUser: int
    idGuild: int
    xp: int
    lvl: int
    lastMessage: datetime

@dataclass()
class MsgReact():
    id: int
    idGuild: int