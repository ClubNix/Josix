import discord
from discord.ext import commands

from database.database import DatabaseHandler

class XP(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseHandler(__file__)


def setup(bot: commands.Bot):
    bot.add_cog(XP(bot))