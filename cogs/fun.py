import discord
from discord.ext import commands

import os
import asyncio
import json
import random

from dotenv import load_dotenv
from blagues_api import *

load_dotenv()
KEY = os.getenv("jokes")
jokes = BlaguesAPI(KEY)

SCRIPT_DIR = os.path.dirname(__file__)
FILE_PATH = os.path.join(SCRIPT_DIR, '../askip.json')

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello !")

    @commands.command(description="Send the message as if it is his own sentence", aliases=["repeat","echo"])
    async def say(self,ctx,*text):
        await ctx.message.delete()
        await ctx.send(" ".join(text))

    @commands.command(description = "Send a random joke", aliases = ["blague", "JOKE"])
    async def joke(self, ctx, jokeType : str = None):
        types = ["global", "dev", "beauf", "blondes", "dark", "limit"]
        disallowCat = []
        is_in_public = ctx.channel.category_id == 751114303314329704
        blg = None

        if (is_in_public):
            disallowCat.append(types.pop())
            disallowCat.append(types.pop())

        if jokeType is None:
            blg = await jokes.random(disallow = disallowCat)

        else:
            jokeType = jokeType.lower()
            if jokeType not in types:
                await ctx.send("Unknown category")
                await ctx.send("Available categories : " + ", ".join(types))
                return

            blg = await jokes.random_categorized(jokeType)

        await ctx.send(blg.joke)
        await asyncio.sleep(1)
        await ctx.send(blg.answer)

    @commands.command(description = "All your private jokes", aliases = ["ASKIP"])
    async def askip(self, ctx, user : str = None):
        with open(FILE_PATH, 'r') as askip:
            credentials = json.load(askip)

        if user is None:
            user = random.choice(list(credentials.keys()))
        
        try:
            blg = random.choice(list(credentials[user].keys()))
            await ctx.send(credentials[user][blg])
        except KeyError as _:
            await ctx.send("Unknown member")

def setup(bot):
    bot.add_cog(Fun(bot))