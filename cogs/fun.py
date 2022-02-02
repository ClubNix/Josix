import discord
from discord.ext import commands

import os
import asyncio
import requests 
import json

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

    @commands.command(description = "Envoie une blague au hasard", aliases = ["blague", "JOKE"])
    async def joke(self, ctx, jokeType : str = None):
        types = ["global", "dev", "beauf", "blondes", "geek", "dark", "limit"]
        disallowCat = []
        is_in_public = ctx.channel.category_id == 751114303314329704
        blg = None

        if (is_in_public):
            disallowCat.append(types.pop())
            disallowCat.append(types.pop())

        if jokeType is None:
            blg = await blagues.random(disallow = disallowCat)

        else:
            jokeType = jokeType.lower()
            if jokeType not in types:
                await ctx.send("Cette catégorie n'existe pas !")
                await ctx.send("Catégories disponibles : " + ", ".join(types))
                return

            if jokeType == "geek":
                response = requests.get('https://geek-jokes.sameerkumar.website/api?format=json')
                blg = response.json()["joke"]
                await ctx.send(blg)
                return

            blg = await blagues.random_categorized(jokeType)

        await ctx.send(blg.joke)
        await asyncio.sleep(1)
        await ctx.send(blg.answer)

    @commands.command(description = "Les privates joke du nix", aliases = ["ASKIP"])
    async def askip(self, ctx):
        pass

def setup(bot):
    bot.add_cog(Fun(bot))