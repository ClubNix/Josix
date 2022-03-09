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
    
    async def vote_askip(self,ctx,message):
        """
        NOT A BOT COMMAND
        process the decision of whether of not the message passed in parameters
        should be saved in the askip json.
        !!! n'ajoute que si plus de 2 votent en faveur & pas de refus
        """

        msg = await ctx.send('is this a good askip ?',reference=message.to_reference())

        reacts = []
        ############# add reaction choices

        for reaction in ['❌','☑️']:
            await msg.add_reaction(reaction)

        ############# function that will be called whenever there is a reaction add. 
        def check(reaction,user):
            if user == commands.bot:    # if the user is josix chan
                return False            # ignore
            return str(reaction)=='❌'  # else, if anyone clicked X, return true (= stop waiting)

        try:    
            await self.bot.wait_for('reaction_add', check=check,timeout=300)    # timeout = 15 minutes=900(it's ok for us, this is a coroutine)    
        
        except asyncio.TimeoutError:                                            # once we have waited for 5 minutes
            if(reacts.count('☑️')>=3 and reacts.count('❌')<=2):                 # if no one disagrees and at least 2 ppl aggree
                await msg.edit(content="OK! askip added!")                      # send fin, return true
                return True
            msg.edit(content="no one agreed. i'm bored waiting. askip not added")
            return False

        await msg.edit(content="someone didn't agree... askip not added")
        return False

    @commands.command(description = "fills my collection of private jokes", aliases = ["ADDASKIP","addaskip"])
    async def add_askip(self,ctx,user=None,joke_name=None, joke=None,*no_more_args):
        """
            saves askip joke in askip.json
            ...but proceeds to nicely ask to us before
        """

        ############# deal with bad command usage

        if(user==None or joke_name==None or joke==None or len(no_more_args)>0):
            await ctx.send("i can't understand :( try \"j!help add_askip\"")
            return

        should_add = await self.vote_askip(ctx,ctx.message) # nicely asks everyone before.

        if not should_add:
            return

        ############# append askip to the credentials json object
        
        credentials = {}
        with open("askip.json", 'r') as askipfile:
            credentials = json.load(askipfile)
        
        if(user not in credentials.keys()):                 # if the member is not registered in the json file
            credentials[user] = {}                          # create a new pair for it
            
        if(name in credentials[user].keys()):
            name = name + str(len(credentials[user]))       # pour éviter la réécriture des askip (à améliorer)

        credentials[user][name] = joke                   # add joke

        ############# update the json file

        with open("askip.json", "w") as askipfile:
            askipfile.write(json.dumps(credentials))        # write new askip file


def setup(bot):
    bot.add_cog(Fun(bot))