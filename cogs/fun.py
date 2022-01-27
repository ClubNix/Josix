import discord
from discord.ext import commands

import os
import asyncio
from dotenv import load_dotenv
from blagues_api import *

load_dotenv()
KEY = os.getenv("blagues")
blagues = BlaguesAPI(KEY)

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coucou(self, ctx):
        await ctx.send("Coucou !")

    @commands.command(description="répète la phrase donnée",aliases=["repeat","echo"])
    async def say(self,ctx,*args):
        await ctx.message.delete()
        await ctx.send(" ".join(args))

<<<<<<< HEAD
    @commands.command(description = "Envoie une blague au hasard", aliases = ["blague", "JOKE"])
    async def joke(self, ctx, type=None):
        types = ["global", "dev", "dark", "limit", "beauf", "blondes"]

        if type is None:
            blg  =  await blagues.random()
        else:
            if type not in types:
                await ctx.send("Cette catégorie n'existe pas !")
                await ctx.send("Catégories disponibles : " + ", ".join(types))
                return
            blg = await blagues.random_categorized(type)

        await ctx.send(blg.joke)
        await asyncio.sleep(1)
        await ctx.send(blg.answer)

=======
>>>>>>> 8ca6f4e5ba0e5324df35286e2dc28417a390251a
def setup(bot):
    bot.add_cog(Fun(bot))