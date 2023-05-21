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
    enableWelcome: bool
    wChan: int
    wRole: int
    wText: str
    logNews: int

@dataclass()
class LinkUserGuild:
    idUser: int
    idGuild: int
    xp: int
    lvl: int
    lastMessage: datetime

@dataclass()
class MsgReact:
    id: int
    idGuild: int

@dataclass()
class ReactCouple:
    id: int
    emoji: str
    idRole: int

@dataclass()
class LogSelection:
    idGuild: int
    logs: list[int]

@dataclass()
class GameType:
    id: int
    name: str
    
@dataclass()
class Game:
    id: int
    idType: int
    idUser: int
    opponent: int