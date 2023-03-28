import discord
from discord.ext import commands, tasks
from discord import ApplicationContext
from discord import option

import random
import datetime

from database.database import DatabaseHandler

FILES = {}

class Usage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()
        self.checkBirthday.start()

    @commands.slash_command(
        description="Get the help menu",
        options=[discord.Option(input_type=str,
                                name="command_name",
                                description="Name of the command",
                                default=None,
                                )]
    )
    async def help(self, ctx: ApplicationContext, command_name: str):
        if not command_name:
            helpEmbed = discord.Embed(title="Help embed",
                                      description=f"Use /help [command_name] to see more info for a command",
                                      color=0x0089FF)
            helpEmbed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
            helpEmbed.set_thumbnail(url=self.bot.user.display_avatar)
            
            gamesCmd = []
            for cogName, cog in self.bot.cogs.items():
                lstCmd = ""

                if not cog or cogName.lower() == "events" or (
                        cogName.lower() == "owner" and not await self.bot.is_owner(ctx.author)):
                    continue

                if cog.description.lower().startswith("games"):
                    for cmd in cog.get_commands():
                        gamesCmd.append(cmd.qualified_name)
                    continue

                commands = cog.get_commands()
                if len(commands) == 0:
                    lstCmd = "No commands available"
                else:
                    for command in commands:
                        lstCmd += "`" + command.qualified_name + "`, "
                    lstCmd = lstCmd[:len(lstCmd) - 2]
                helpEmbed.add_field(name=cogName, value=lstCmd, inline=False)

            if len(gamesCmd) > 0:
                helpEmbed.add_field(name="Games", value="`" + "`, `".join(gamesCmd) + "`", inline=False)
            await ctx.respond(embed=helpEmbed)

        else:
            command_name = command_name.lower()
            command: discord.SlashCommand = self.bot.get_application_command(name=command_name,
                                                                             type=discord.SlashCommand)

            if not command:
                await ctx.respond(f":x: Unknown command, see /help :x:")
                return

            if command.cog and command.cog.qualified_name.lower() == "owner" and not await self.bot.is_owner(
                    ctx.author):
                await ctx.respond(f":x: Unknown command, see /help :x:")
                return

            if command.description == "":
                desc = "No description"
            else:
                desc = command.description

            usage = f"/{command.name} "
            param = command.options
            options = ""

            for val in param:
                default = val.default
                if default:
                    default = f" = {default}"
                else:
                    default = ""

                if val.required:
                    usage += f"<{val.name}{default}> "
                else:
                    usage += f"[{val.name}{default}] "

                options += f"**{val.name}** : {val.description}\n"

            embed2 = discord.Embed(title="Help command",
                                   description=f"Description of the command **{command.name}**\n <> -> Required "
                                               f"parameters | [] -> Optional parameters",
                                   color=0x0089FF)
            embed2.set_thumbnail(url=self.bot.user.display_avatar)
            embed2.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
            embed2.add_field(name="Description :", value=desc)
            embed2.add_field(name="Usage :", value=usage, inline=False)
            embed2.add_field(name="Options : ", value=options, inline=False)
            await ctx.respond(embed=embed2)

    @commands.slash_command(
        description="Randomly choose a sentence from a list",
        options=[discord.Option(input_type=str,
                                name="sentences",
                                description="List of sentences separated by a `;`",
                                required=True
                                )]
    )
    async def choose(self, ctx: ApplicationContext, sentences: str):
        values = sentences.split(";")
        embed = discord.Embed(title="Result", description=random.choice(values))
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        await ctx.respond(embed=embed)

    @commands.slash_command(
        description="Close a thread in the forum channel. Can only be used by the creator of the thread or a moderator")
    @commands.guild_only()
    @option(
        name="lock",
        description="Lock the thread (moderator only)",
        type=bool,
        default=False
    )
    async def close(self, ctx: ApplicationContext, lock: bool):
        thread = ctx.channel
        if not (isinstance(thread, discord.Thread) and isinstance(thread.parent, discord.ForumChannel)):
            await ctx.respond("You can only close a thread created in the forum")
            return

        testMod = ctx.author.guild_permissions.manage_threads  # Check if permissions are greater than manage_threads
        if (ctx.author != thread.owner and not testMod) or (lock and not testMod):
            await ctx.respond("You don't have the required permissions to do this")
            return

        await ctx.respond(f"Closing the thread.\nLocking : {lock}")
        await thread.archive(locked=lock)

    @commands.slash_command(description="Add your birthday in the database !")
    @commands.guild_only()
    @option(
        input_type=int,
        name="day",
        description="Day number of your birthday",
        required=True
    )
    @option(
        input_type=int,
        name="month",
        description="Month number of your birthday",
        required=True
    )
    @option(
        input_type=discord.User,
        name="user",
        description="Mention of the user's birthday you want to add",
        default=None
    )
    async def add_birthday(self, ctx: ApplicationContext, day: int, month: int, user: discord.User):
        month_days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        testReject = not ((1 <= month and month <= 12) and (1 <= day and day <= month_days[month - 1]))
        userId = ctx.author.id
        testUser = None
        testGuild = None
        testBoth = None
        bdYear = 0
        stringRes = ""

        if testReject:
            await ctx.respond("Invalid date !")
            return

        if user and user != ctx.author:
            if ctx.author.guild_permissions.moderate_members:
                userId = user.id
                stringRes = f"Birthday added for **{user.name}** !"
            else:
                await ctx.respond("Sorry but you lack permissions (skill issue)")
                return
        else:
            stringRes = "Your birthday has been added !"

        testUser = self.db.getUser(userId)
        if not testUser or len(testUser) == 0:
            self.db.addUser(userId)

        testGuild = self.db.getGuild(ctx.guild_id)
        if not testGuild or len(testGuild) == 0:
            self.db.addGuild(ctx.guild_id)

        testBoth = self.db.getUserInGuild(userId, ctx.guild_id)
        if not testBoth or len(testBoth) == 0:
            self.db.addUserGuild(userId, ctx.guild_id)

        today = datetime.date.today()
        if today.month < month or (today.month == month and today.day < day):
            bdYear = today.year - 1
        else:
            bdYear = today.year

        self.db.updateUserBD(userId, day, month, bdYear)
        await ctx.respond(stringRes)

    def getMonthField(self, embed: discord.Embed, idGuild: int, monthInt: int):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                  "November", "December"]
        res = []

        values = self.db.getBDMonth(idGuild, monthInt)
        if values is None or len(values) == 0:
            return embed

        for val in values:
            res.append(f"`{val[0]}/{val[1]}` (<@{val[2]}>)")

        return embed.add_field(name=months[monthInt - 1], value=" , ".join(res))

    @commands.slash_command(description="See all the birthdays of this server")
    @commands.guild_only()
    @option(
        input_type=int,
        name="month",
        description="Number of the month you want to get all the birthdays from",
        min_value=1,
        max_value=12,
        default=None
    )
    async def birthdays(self, ctx: ApplicationContext, month: int):
        embed = discord.Embed(
            title=f"Birthdays of **{ctx.guild.name}**",
            description="All the birthdays form the server",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)

        if month:
            embed = self.getMonthField(embed, ctx.guild_id, month)
        else:
            for i in range(12):
                embed = self.getMonthField(embed, ctx.guild_id, i + 1)
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Get the birthday of a user")
    @commands.guild_only()
    @option(
        input_type=discord.User,
        name="user",
        description="Mention of the user",
        required=True
    )
    async def user_birthday(self, ctx: ApplicationContext, user: discord.User):
        res = self.db.getBDUser(user.id)
        if not res or len(res) == 0:
            await ctx.respond("User not registered")
            return

        embed = discord.Embed(title=f"Birthday of {user}", color=0x0089FF)
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.add_field(name="Date", value=res[0])
        await ctx.respond(embed=embed)

    @tasks.loop(hours=6.0)
    async def checkBirthday(self):
        today = datetime.date.today()
        bd = self.db.checkBD(today.day, today.month)

        for value in bd:
            idUser = value[0]
            results = self.db.getNewsChan(idUser)

            for row in results:
                chan = self.bot.get_channel(row[0])
                if not chan:
                    continue

                today = datetime.date.today()
                await chan.send(f"Happy birthday to <@{idUser}> :tada: !")
                self.db.updateUserBD(idUser, today.day, today.month, today.year)


def setup(bot: commands.Bot):
    bot.add_cog(Usage(bot))
