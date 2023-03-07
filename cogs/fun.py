import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option

import os
import json
import random

from blagues_api import BlaguesAPI
from aiohttp import ClientResponseError
from asyncio import TimeoutError
from dotenv import load_dotenv
from json import JSONDecodeError

load_dotenv()
KEY = os.getenv("jokes")
jokes = BlaguesAPI(KEY)

SCRIPT_DIR = os.path.dirname(__file__)
FILE_PATH = os.path.join(SCRIPT_DIR, '../askip.json')

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def checkJson(self, file: dict) -> bool:
        return (file.keys()) or (len(file.keys()) > 0)
        

    @commands.slash_command(description="The bot greets you")
    async def hello(self, ctx: ApplicationContext):
        await ctx.respond("Hello !")

    @commands.slash_command(description="Ping the bot !")
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def ping(self, ctx: ApplicationContext):
        av_aut = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar

        embed = discord.Embed(title="Pong !", color=0x0089FF)
        embed.set_author(name=ctx.author, icon_url=av_aut)
        embed.set_thumbnail(url="https://media.giphy.com/media/fvA1ieS8rEV8Y/giphy.gif")
        embed.add_field(name="", value=f"Ping : {round(self.bot.latency*1000, 2)} ms")
        await ctx.respond(embed=embed)

    @commands.slash_command(
        description="Send the message with the bot as the author and delete yours",
        options=[discord.Option(
            input_type=str,
            name="text",
            description="The sentence that will be repeated",
            required=True
        )]
    )
    async def say(self, ctx: ApplicationContext, text: str):
        await ctx.delete()
        await ctx.respond("".join(text))

    @commands.slash_command(description="Send a random joke")
    @option(
        input_type=int,
        name="joke_type",
        description="Category of the joke",
        default=None,
        choices=[
            discord.OptionChoice(name="None 🎲", value=-1),
            discord.OptionChoice(name="Global 🤡", value=0),
            discord.OptionChoice(name="Dev 💻", value=1),
            discord.OptionChoice(name="Beauf 🍺", value=2),
            discord.OptionChoice(name="Blondes 👱‍♀️", value=3),
            discord.OptionChoice(name="Dark 😈", value=4),
            discord.OptionChoice(name="Limit 🍑", value=5),
        ]
    )
    async def joke(self, ctx: ApplicationContext, joke_type: int):
        # To prevent some jokes in a category, put the ID of the category here
        is_in_public = ctx.channel.category_id == 751114303314329704 
        disallowCat = []
        types = ["global", "dev", "beauf", "blondes", "dark", "limit"]
        blg = None
        av_aut = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar

        if (is_in_public):
            disallowCat.append(types.pop())
            disallowCat.append(types.pop())

            if joke_type >= 4:
                await ctx.respond("You are not permitted to use this type of joke here")
                return

        if joke_type is None or joke_type == -1:
            try:
                blg = await jokes.random(disallow=disallowCat)
            except ClientResponseError:
                await ctx.respond("Token error")
                return

        else:
            try:
                blg = await jokes.random_categorized(types[joke_type])
            except ClientResponseError:
                await ctx.respond("Token error")
                return

        embed = discord.Embed(title=blg.joke, description=f"||{blg.answer}||", color=0x0089FF)
        embed.set_author(name=ctx.author, icon_url=av_aut)
        await ctx.respond(embed=embed)

    @commands.slash_command(
        description="See all the people that got one or more askip",
        options=[discord.Option(
            input_type=str,
            name="username",
            description="List all the askip of a specific user",
            default=None
        )]
    )
    @commands.guild_only()
    async def list_askip(self, ctx: ApplicationContext, username: str):
        data = None

        try:
            if username:
                username = username.lower()

                with open(FILE_PATH, 'r') as askip:
                    lst = json.load(askip)
                    try:
                        if not self.checkJson(lst[username]):
                            await ctx.respond("Empty value")
                            return

                        data = lst[username].keys()
                    except KeyError:
                        cmd = self.bot.get_application_command("list_askip", type=discord.commands.core.ApplicationCommand)
                        await ctx.invoke(cmd, user=None)
                        return

            else:
                with open(FILE_PATH, 'r') as askip:
                    data = json.load(askip).keys()
            await ctx.respond("Available names : `" + "`, `".join(data) + "`")

        except JSONDecodeError:
            await ctx.respond("Empty json file")
            return

    @commands.slash_command(
        description = "Get a private joke from your group",
        options=[
            discord.Option(
                input_type=str,
                name="username",
                description="Name of the user you want an askip from (take a random user if no user is given)",
                default=None
            ),
            discord.Option(
                input_type=str,
                name="askip_name",
                description="Name of an askip you searching (take a random askip if no name is given)",
                default=None
            )
        ]
    )
    @commands.guild_only()
    async def askip(self, ctx: ApplicationContext, username: str, askip_name: str):
        try:
            with open(FILE_PATH, 'r') as askip:
                credentials = json.load(askip)
                if not self.checkJson(credentials):
                    await ctx.respond("Empty value or json file")
                    return 

        except JSONDecodeError:
            await ctx.respond("Empty json file")
            return

        if askip_name and not username:
            await ctx.respond("To choose a specific askip you need to specify the user")
            return
            
        if username:
            username = username.lower()
        else:
            username = random.choice(list(credentials.keys()))

        if not self.checkJson(credentials[username]):
            await ctx.respond("Empty value or json file")
            return
        
        try:
            if askip_name:
                blg = askip_name
            else:
                blg = random.choice(list(credentials[username].keys()))

            await ctx.respond(credentials[username][blg])
        except KeyError:
            await ctx.respond("Unknown member or askip\nAvailable names : `" + "`, `".join(credentials.keys()) + "`")
    
    async def vote_askip(self, ctx: ApplicationContext, ask_aut: str, ask_name: str, ask_text: str):
        """
        NOT A BOT COMMAND
        process the decision of whether of not the message passed in parameters
        should be saved in the askip json.
        !!! Add it only if 2 members agrees and none disagrees
        """

        av_aut = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar
        waitColor = 0x237bd9
        yesColor = 0x1cb82b
        noColor = 0xc90e3a

        askEmbed = discord.Embed(
            title="Is this a good askip ?",
            description="The results will be gathered after 5 minutes 🕘",
            color=waitColor
        )
        askEmbed.set_author(name=ctx.author, icon_url=av_aut)
        askEmbed.add_field(
            name="Conditions",
            value="To add this askip i need two agreements (✅) and no disagreement (❌)",
            inline=False
        )
        askEmbed.add_field(
            name="Summary",
            value=f"User : `{ask_aut}` \nName : `{ask_name}` \nContent : `{ask_text}`"
        )

        yesEmbed = askEmbed.copy()
        

        yesEmbed.description = "Results gathered, askip added ! ✅"
        yesEmbed.color = yesColor

        noEmbed = askEmbed.copy()
        noEmbed.color = noColor

        reacts = []
        msg : discord.Interaction = await ctx.respond(embed=askEmbed)
        og = await msg.original_response()

        ############# add reaction choices

        for reaction in ['✅','❌']:
            await og.add_reaction(reaction)

        ############# function that will be called whenever there is a reaction add. 
        def check(reaction,user):
            if user == commands.bot:    # if the user is josix chan
                return False                                  # ignore
            reacts.append(str(reaction))
            return str(reaction)=='❌'  # else, if anyone clicked X, return true (= stop waiting)

        try:    
            await self.bot.wait_for('reaction_add', check=check,timeout=300)    # timeout = 15 minutes=900(it's ok for us, this is a coroutine)    
        
        except TimeoutError:                                                    # once we have waited for 5 minutes
            if(reacts.count('❌') < 1 and reacts.count('✅') > 1):              # if no one disagrees and at least 2 ppl aggree
                await og.edit(embed=yesEmbed)  # send fin, return true
                return True

            noEmbed.description = "No one agreed. i'm bored waiting. askip not added ! ❌"
            await og.edit(embed=noEmbed)
            return False

        noEmbed.description = "Someone didn't agree, askip not added ! ❌"
        await og.edit(embed=noEmbed)
        return False

    @commands.slash_command(description = "fills my collection of private jokes")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    @option(
        input_type=str,
        name="username",
        description="Name of the user who get this askip",
        required=True
    )
    @option(
        input_type=str,
        name="askip_name",
        description="Name of the new askip",
        required=True
    )
    @option(
        input_type=str,
        name="askip_text",
        description="Content of the askip",
        required=True
    )
    async def add_askip(self, ctx: ApplicationContext, username: str, askip_name: str, askip_text: str):
        """
            saves askip joke in askip.json
            ...but proceeds to nicely ask to us before
        """

        username = username.lower()
        askip_name = askip_name.lower()
        credentials = {}
    
        try:
            with open("askip.json", 'r') as askipfile:
                credentials = json.load(askipfile)
        except JSONDecodeError:
            await ctx.respond("Empty json file")
            return

        try:
            if askip_name in credentials[username].keys():
                await ctx.respond("This askip already exists")
                return
        except KeyError:
            pass

        should_add = await self.vote_askip(ctx, username, askip_name, askip_text) # nicely asks everyone before.
        if not should_add:
            return

        ############# append askip to the credentials json object
        
        if(username not in credentials.keys()):                 # if the member is not registered in the json file
            credentials[username] = {}                          # create a new pair for it

        credentials[username][askip_name] = askip_text               # add joke

        ############# update the json file
        with open("askip.json", "w") as askipfile:
            askipfile.write(json.dumps(credentials, indent=4))  # write new askip file


    @commands.slash_command(description="Get the avatar of someone")
    @option(
        input_type=discord.User,
        name="user",
        description="Mention of the user you want to get the avatar from",
        default=None
    )
    async def avatar(self, ctx: ApplicationContext, user: discord.User):
        if user is None:
            user = ctx.author

        embed = discord.Embed(title=f"The avatar of {user}", color=0x0089FF)
        embed.set_image(url=user.avatar.url if user.avatar else user.default_avatar)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar)
        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
