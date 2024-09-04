import datetime as dt
import json
import os
import random
from asyncio import TimeoutError
from json import JSONDecodeError

import discord
from aiohttp import ClientResponseError
from blagues_api import BlaguesAPI  # type: ignore
from discord import ApplicationContext, Interaction, WebhookMessage, option
from discord.ext import commands
from dotenv import load_dotenv

from cogs.xp_system import XP
from database.services import discord_service, xp_service
from josix import Josix
from pkg.bot_utils import JosixCog, josix_slash


class Fun(JosixCog):
    """
    Represents the fun functionalities extension of the bot

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    jokes : BlaguesAPI
        Instance to perform requests on a french jokes generator API
    """

    load_dotenv(".env.dev")
    _KEY = os.getenv("JOKES")
    _SCRIPT_DIR = os.path.dirname(__file__)
    _FILE_PATH = os.path.join(_SCRIPT_DIR, '../askip.json')

    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot
        self.jokes = BlaguesAPI(Fun._KEY)

    def checkJson(self, file: dict) -> bool:
        return bool(file.keys()) or (len(file.keys()) > 0)

    @josix_slash(description="The bot greets you")
    async def hello(self, ctx: ApplicationContext):
        await ctx.respond("Hello !")

    @josix_slash(description="Ping the bot !")
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def ping(self, ctx: ApplicationContext):
        embed = discord.Embed(title="Pong !", color=0x0089FF)
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.set_thumbnail(url="https://media.giphy.com/media/fvA1ieS8rEV8Y/giphy.gif")
        embed.add_field(name="", value=f"Ping : {round(self.bot.latency*1000, 2)} ms")
        await ctx.respond(embed=embed)

    @josix_slash(
        description="Send the message as if it is his own sentence",
        options=[discord.Option(
            input_type=str,
            name="text",
            description="The sentence that will be repeated",
            max_length=512,
            required=True
        )]
    )
    @discord.default_permissions(manage_messages=True)
    async def say(self, ctx: ApplicationContext, text: str):
        await ctx.send(text)
        await ctx.delete()

    @josix_slash(description="Send a random joke")
    @option(
        input_type=int,
        name="joke_type",
        description="Category of the joke",
        default=-1,
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
        await ctx.defer(ephemeral=False, invisible=False)
        
        # To prevent some jokes in a category, put the ID of the category here
        is_in_public = ctx.channel.category_id == 751114303314329704 
        disallowCat = []
        types = ["global", "dev", "beauf", "blondes", "dark", "limit"]
        blg = None

        if (is_in_public):
            disallowCat.append(types.pop())
            disallowCat.append(types.pop())

            if joke_type >= 4:
                await ctx.respond("You are not permitted to use this type of joke here")
                return

        if joke_type is None or joke_type == -1:
            try:
                blg = await self.jokes.random(disallow=disallowCat)
            except ClientResponseError:
                await ctx.respond("Token error")
                return

        else:
            try:
                blg = await self.jokes.random_categorized(types[joke_type])
            except ClientResponseError:
                await ctx.respond("Token error")
                return

        embed = discord.Embed(title=blg.joke, description=f"||{blg.answer}||", color=0x0089FF)
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        await ctx.respond(embed=embed)

    @josix_slash(
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

                with open(Fun._FILE_PATH, 'r') as askip:
                    lst = json.load(askip)
                    try:
                        if not self.checkJson(lst[username]):
                            await ctx.respond("Empty value")
                            return

                        data = lst[username].keys()
                    except KeyError:
                        cmd = self.bot.get_application_command(
                            "list_askip",
                            type=discord.commands.core.ApplicationCommand
                        )
                        if cmd is None:
                            await ctx.respond("Error encountered on the listing")
                            return
                        await ctx.invoke(cmd, user=None)
                        return

            else:
                with open(Fun._FILE_PATH, 'r') as askip:
                    data = json.load(askip).keys()
            await ctx.respond("Available names : `" + "`, `".join(data) + "`")

        except JSONDecodeError:
            await ctx.respond("Empty json file")
            return

    @josix_slash(
        description="Get a private joke from your group",
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
                default=""
            )
        ]
    )
    @commands.guild_only()
    async def askip(self, ctx: ApplicationContext, username: str, askip_name: str):
        try:
            with open(Fun._FILE_PATH, 'r') as askip:
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
        
        userParam = False
        if username:
            username = username.lower()
            userParam = True
        else:
            username = random.choice(list(credentials.keys()))
        
        try:
            if not self.checkJson(credentials[username]):
                await ctx.respond("Empty value or json file")
                return
                
            if askip_name:
                blg = askip_name
            else:
                blg = random.choice(list(credentials[username].keys()))

            res = f"**{username}** : " if not userParam else ""
            res += credentials[username][blg]
            await ctx.respond(res)
        except KeyError:
            await ctx.respond("Unknown member or askip\nAvailable names : `" + "`, `".join(credentials.keys()) + "`")
    
    async def vote_askip(self, ctx: ApplicationContext, ask_aut: str, ask_name: str, ask_text: str) -> bool | None:
        """
        NOT A BOT COMMAND
        process the decision of whether of not the message passed in parameters
        should be saved in the askip json.
        !!! Add it only if 2 members agrees and none disagrees
        """

        waitColor = 0x237bd9
        yesColor = 0x1cb82b
        noColor = 0xc90e3a

        askEmbed = discord.Embed(
            title="Is this a good askip ?",
            description="The results will be gathered after 5 minutes 🕘",
            color=waitColor
        )
        askEmbed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
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
        yesEmbed.colour = discord.Colour(yesColor)

        noEmbed = askEmbed.copy()
        noEmbed.colour = discord.Colour(noColor)

        reacts = []
        msg: Interaction | WebhookMessage = await ctx.respond(embed=askEmbed)
        if isinstance(msg, WebhookMessage):
            await ctx.send("Unexpected error during process")
            return None

        og = await msg.original_response()

        # add reaction choices

        for reaction in ['✅', '❌']:
            await og.add_reaction(reaction)

        # function that will be called whenever there is a reaction add.
        def check(reaction: discord.Reaction, user: discord.User):
            if user.bot:    # if the user is a bot
                return False   # ignore
            reacts.append(str(reaction))
            return False

        try:
            # timeout = 15 minutes=900(it's ok for us, this is a coroutine)
            await self.bot.wait_for('reaction_add', check=check, timeout=180)
        
        except TimeoutError:  # once we have waited for 5 minutes
            # if no one disagrees and at least 2 ppl aggree
            if(reacts.count('❌') < 1 and reacts.count('✅') > 1):
                await og.edit(embed=yesEmbed)  # send fin, return true
                return True

            noEmbed.description = "No one agreed. i'm bored waiting. askip not added ! ❌"
            await og.edit(embed=noEmbed)
            return False

        noEmbed.description = "Someone didn't agree, askip not added ! ❌"
        await og.edit(embed=noEmbed)
        return False

    @josix_slash(description="fills my collection of private jokes", give_xp=True)
    @commands.guild_only()
    @option(
        input_type=str,
        name="username",
        description="Name of the user who get this askip",
        max_length=64,
        required=True
    )
    @option(
        input_type=str,
        name="askip_name",
        description="Name of the new askip",
        max_length=64,
        required=True
    )
    @option(
        input_type=str,
        name="askip_text",
        description="Content of the askip",
        max_length=512,
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
        handler = self.bot.get_handler()
    
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

        should_add = await self.vote_askip(ctx, username, askip_name, askip_text)  # nicely asks everyone before.
        if not should_add:
            return

        # append askip to the credentials json object
        
        if(username not in credentials.keys()):  # if the member is not registered in the json file
            credentials[username] = {}  # create a new pair for it

        credentials[username][askip_name] = askip_text  # add joke

        # update the json file
        with open("askip.json", "w") as askipfile:
            askipfile.write(json.dumps(credentials, indent=4))  # write new askip file

        guild = ctx.guild
        idAuth = ctx.author.id
        amount = 100
        _, _, userGuildDB = discord_service.fetch_user_guild_relationship(handler, idAuth, guild.id)

        if userGuildDB is None:
            await ctx.respond("Unexpected data error")
            return
        if userGuildDB.isUserBlocked:
            return

        currentXP = userGuildDB.xp
        newXP, level = XP.checkUpdateXP(currentXP, amount)
        xp_service.update_user_xp(handler, idAuth, guild.id, level, newXP, dt.datetime.now())


    @josix_slash(description="Get the avatar of someone")
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
        embed.set_image(url=user.display_avatar)
        await ctx.respond(embed=embed)


def setup(bot: Josix):
    bot.add_cog(Fun(bot, True))
