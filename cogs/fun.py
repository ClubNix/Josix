import discord
from discord.ext import commands
from discord import ApplicationContext

import os
import json
import random
import blagues_api

from aiohttp import ClientResponseError
from asyncio import TimeoutError
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("jokes")
jokes = blagues_api.BlaguesAPI(KEY)

SCRIPT_DIR = os.path.dirname(__file__)
FILE_PATH = os.path.join(SCRIPT_DIR, '../askip.json')

class Fun(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot

    @commands.slash_command(description="The bot greets you")
    async def hello(self, ctx : ApplicationContext):
        await ctx.respond("Hello !")

    @commands.slash_command(
        description="Send the message with the bot as the author and delete yours",
        options=[discord.Option(
            input_type=str,
            name="text",
            description="The sentence that will be repeated",
            required=True
        )]
    )
    async def say(self,ctx : ApplicationContext, text : str):
        await ctx.delete()
        await ctx.respond("".join(text))

    @commands.slash_command(
        description = "Send a random joke",
        options=[discord.Option(
            input_type=str,
            name="joke_type",
            description="Category of the joke",
            default=None
        )]
    )
    async def joke(self, ctx : ApplicationContext, jokeType : str):
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
                await ctx.respond("Token error")
                return

        else:
            jokeType = jokeType.lower()
            if jokeType not in types:
                await ctx.respond("Unknown category")
                await ctx.respond("Available categories : " + ", ".join(types))
                return

            try:
                blg = await jokes.random_categorized(jokeType)
            except ClientResponseError as _:
                await ctx.respond("Your token is wrong")
                return

        await ctx.respond(blg.joke + "\n" + blg.answer)

    @commands.slash_command(description="See all the people that got one or more askip")
    async def list_askip(self, ctx : ApplicationContext):
        with open(FILE_PATH, 'r') as askip:
            names = json.load(askip).keys()
        await ctx.respond("Available names : `" + "`, `".join(names) + "`")

    @commands.slash_command(
        description = "All your private jokes",
        options=[discord.Option(
            input_type=str,
            name="username",
            description="Name of the user you want a askip from",
            required=False
        )]
    )
    async def askip(self, ctx : ApplicationContext, user : str = None):
        with open(FILE_PATH, 'r') as askip:
                credentials = json.load(askip)

        if user is None:
            user = random.choice(list(credentials.keys()))
        else:
            user = user.lower()
        
        try:
            blg = random.choice(list(credentials[user].keys()))
            await ctx.respond(credentials[user][blg])
        except KeyError as _:
            await ctx.respond("Unknown member")
            await ctx.respond("Available names : `" + "`, `".join(credentials.keys()) + "`")
    
    async def vote_askip(self,ctx : ApplicationContext, message : discord.Message):
        """
        NOT A BOT COMMAND
        process the decision of whether of not the message passed in parameters
        should be saved in the askip json.
        !!! Add it only if 2 members agrees and none disagrees
        """

        reacts = []
        msg : discord.Interaction = await ctx.respond('is this a good askip ? \nThe results will be gathered after 5 minutes')
        og = await msg.original_response()

        ############# add reaction choices

        for reaction in ['✅','❌']:
            await og.add_reaction(reaction)

        ############# function that will be called whenever there is a reaction add. 
        def check(reaction,user):
            if user == commands.bot:    # if the user is josix chan
                return False            # ignore
            reacts.append(str(reaction))
            return str(reaction)=='❌'  # else, if anyone clicked X, return true (= stop waiting)

        try:    
            await self.bot.wait_for('reaction_add', check=check,timeout=300)    # timeout = 15 minutes=900(it's ok for us, this is a coroutine)    
        
        except TimeoutError:                                                    # once we have waited for 5 minutes
            if(reacts.count('❌') < 1 and reacts.count('✅') > 1):              # if no one disagrees and at least 2 ppl aggree
                await og.edit(content="OK! askip added!")  # send fin, return true
                return True
            await og.edit(content="no one agreed. i'm bored waiting. askip not added")
            return False

        await og.edit(content="someone didn't agree... askip not added")
        return False

    @commands.slash_command(
        description = "fills my collection of private jokes",
        option=[
            discord.Option(
                input_type=str,
                name="username",
                description="Name of the user who get this askip",
                required=True),
            discord.Option(
                input_type=str,
                name="askip_name",
                description="Name of the new askip",
                required=True
            ),
            discord.Option(
                input_type=str,
                name="askip_text",
                description="Content of the askip",
                required=True
            )]
    )
    @commands.has_permissions(moderate_members=True)
    async def add_askip(self, ctx : ApplicationContext, username : str, askip_name : str, askip_text : str):
        """
            saves askip joke in askip.json
            ...but proceeds to nicely ask to us before
        """

        username = username.lower()
        askip_name = askip_name.lower()
        joke_string = "".join(askip_text)

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


    @commands.slash_command(
        description="Get the avatar of someone",
        options=[discord.Option(
            input_type=discord.Member,
            name="user",
            description="Mention of the user you want to get the avatar",
            default=None
        )]
    )
    async def avatar(self, ctx : ApplicationContext, user : discord.Member):
        if user is None:
            user = ctx.author

        embed = discord.Embed(title=f"The avatar of {user}", color=0x0089FF)
        embed.set_image(url=user.avatar.url if user.avatar else user.default_avatar)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
        await ctx.respond(embed=embed)


def setup(bot : commands.Bot):
    bot.add_cog(Fun(bot))
