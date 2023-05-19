import discord
from discord.ext import commands

from database.database import DatabaseHandler
from enum import Enum

import os

class Logs(Enum):
    AUTOMOD = 1
    GUILD_UPDATE = 2
    CHANNEL_LIFE = 3
    CHANNEL_UPDATE = 4
    ROLE_LIFE = 5
    ROLE_UPDATE = 6
    EMOJIS_UPDATE = 7
    STICKERS_UPDATE = 8
    WEBHOOKS_UPDATE = 9
    BANS = 10
    MEMBER_JOIN = 11
    USER_UPDATE = 12


class Logger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))
        self._updateLogs()

    def _updateLogs(self):
        logs = [(i.lower(), v.value) for i, v in Logs._member_map_.items()]
        self.db.updateLogsEntries(logs)

def setup(bot: commands.Bot):
    bot.add_cog(Logger(bot))
