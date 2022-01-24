import discord
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coucou(self, ctx):
        await ctx.send("Coucou !")

    @commands.command(description="répète la phrase donnée",aliases=["repeat","echo"])
    async def say(self,ctx,*args):
        await ctx.message.delete()
        await ctx.send("\""+" ".join(args)+"\"")

def setup(bot):
    bot.add_cog(Fun(bot))
