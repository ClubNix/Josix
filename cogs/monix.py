import discord 
from discord.ext import commands

class Monix(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(Monix(bot))