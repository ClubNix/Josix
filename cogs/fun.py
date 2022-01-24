import discord
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coucou(self, ctx):
        await ctx.send("Coucou !")

def setup(bot):
    bot.add_cog(Fun(bot))