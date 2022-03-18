import discord
from discord.ext import commands

import os
import asyncio
import json
import random

from aiohttp import ClientResponseError
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
            try:
                blg = await jokes.random(disallow = disallowCat)
            except ClientResponseError as _:
                await ctx.send("Your token is wrong")
                return

        else:
            jokeType = jokeType.lower()
            if jokeType not in types:
                await ctx.send("Unknown category")
                await ctx.send("Available categories : " + ", ".join(types))
                return

            try:
                blg = await jokes.random_categorized(jokeType)
            except ClientResponseError as _:
                await ctx.send("Your token is wrong")
                return

        await ctx.send(blg.joke)
        await asyncio.sleep(1)
        await ctx.send(blg.answer)

    @commands.command(description="See all the people that got one or more askip")
    async def list_askip(self, ctx):
        with open(FILE_PATH, 'r') as askip:
            names = json.load(askip).keys()
        await ctx.send("Available names : `" + "`, `".join(names) + "`")

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
            await ctx.send("Available names : `" + "`, `".join(credentials.keys()) + "`")
    
    async def vote_askip(self,ctx,message):
        """
        NOT A BOT COMMAND
        process the decision of whether of not the message passed in parameters
        should be saved in the askip json.
        !!! Add it only if 2 members agrees and none disagrees
        """

        reacts = []
        msg = await ctx.send('is this a good askip ? \nThe results will be gathered after 5 minutes',reference=message.to_reference())

        ############# add reaction choices

        for reaction in ['❌','✅']:
            await msg.add_reaction(reaction)

        ############# function that will be called whenever there is a reaction add. 
        def check(reaction,user):
            if user == commands.bot:    # if the user is josix chan
                return False            # ignore
            reacts.append(str(reaction))
            print(reacts)
            return str(reaction)=='❌'  # else, if anyone clicked X, return true (= stop waiting)

        try:    
            await self.bot.wait_for('reaction_add', check=check,timeout=300)    # timeout = 15 minutes=900(it's ok for us, this is a coroutine)    
        
        except asyncio.TimeoutError:                                            # once we have waited for 5 minutes
            if(reacts.count('❌') < 1 and reacts.count('✅') > 1):                 # if no one disagrees and at least 2 ppl aggree
                await msg.edit(content="OK! askip added!")  # send fin, return true
                return True
            await msg.edit(content="no one agreed. i'm bored waiting. askip not added")
            return False

        await msg.edit(content="someone didn't agree... askip not added")
        return False

    @commands.command(description = "fills my collection of private jokes", aliases = ["ADDASKIP","addaskip"])
    @commands.has_permissions(manage_messages=True)
    async def add_askip(self, ctx, username=None, askip_name=None, *askip_text):
        """
            saves askip joke in askip.json
            ...but proceeds to nicely ask to us before
        """

        ############# deal with bad command usage
        if(username==None or askip_name==None or len(askip_text)==0):
            await ctx.send("The command is incomplete see `j!help add_askip`\"")
            return

        username = username.lower()
        askip_name = askip_name.lower()
        joke_string = " ".join(askip_text)

        should_add = await self.vote_askip(ctx, ctx.message) # nicely asks everyone before.
        if not should_add:
            return

        ############# append askip to the credentials json object
        credentials = {}
        with open("askip.json", 'r') as askipfile:
            credentials = json.load(askipfile)
        
        if(username not in credentials.keys()):                 # if the member is not registered in the json file
            credentials[username] = {}                          # create a new pair for it
            
        name = askip_name + str(len(credentials[username])) if(askip_name in credentials[username].keys()) else askip_name     # pour éviter la réécriture des askip (à améliorer)
        credentials[username][name] = joke_string               # add joke

        ############# update the json file
        with open("askip.json", "w") as askipfile:
            askipfile.write(json.dumps(credentials, indent=4))        # write new askip file


def setup(bot):
    bot.add_cog(Fun(bot))
