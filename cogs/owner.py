import json
import os
from json import JSONDecodeError

import discord
from discord import ApplicationContext, option
from discord.ext import tasks
from psycopg2 import Error as DBError

import pkg.logwrite as log
from database.services import discord_service
from josix import Josix
from pkg.bot_utils import JosixCog, josix_slash
from pkg.logwrite import ERROR_FILE, LOG_FILE


class Owner(JosixCog):
    """
    Represents the Owner functions extension of the bot

    By default it also allows the administrator of servers to perform these commands
    because it was better to handle for the Club*Nix

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    """

    _SCRIPT_DIR = os.path.dirname(__file__)
    _SQL_FILE = os.path.join(_SCRIPT_DIR, '../database/backup.sql')
    _CONFIG_FILE = os.path.join(_SCRIPT_DIR, '../configs/config.json')
    
    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp, isOwner=True)
        self.bot = bot
        self.startup = True

        try:
            with open(Owner._CONFIG_FILE, 'r') as f:
                data = json.load(f)

            self.report = data["report_channel"]
        except JSONDecodeError as _:
            self.report = 0

        self.daily_backup.start()
        self.check_connection.start()

    def cog_check(self, ctx: ApplicationContext):
        """Check automatically called for every command of this cog"""
        return self.bot.is_owner(ctx.author) or ctx.author.guild_permissions.administrator

    @josix_slash(description="Stop the bot")
    async def stop_josix(self, ctx: ApplicationContext):
        await ctx.respond("Stopping...")
        await self.bot.close()

    @josix_slash(description="Create a backup for the database")
    @option(
        input_type=str,
        name="table",
        description="Name of the table to backup",
        default=""
    )
    async def create_backup(self, ctx: ApplicationContext, table: str):
        await ctx.defer(ephemeral=False, invisible=False)
        self.bot.db.backup(table)
        await ctx.respond("Backup done !")

    @josix_slash(description="Execute a query")
    @option(
        input_type=str,
        name="query",
        description="Query to execute",
        required=True
    )
    async def execute(self, ctx: ApplicationContext, query: str):
        await ctx.defer(ephemeral=False, invisible=False)
        try:
            await ctx.respond(self.bot.db.execute(query))
        except discord.HTTPException as e:
            await ctx.respond(e)

    @josix_slash(description="Execute the backup file")
    async def execute_backup(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        count = 0
        tmp = ""
        msg = ""

        with open(Owner._SQL_FILE, 'r') as f:
            lines = f.readlines()
        for index, line in enumerate(lines):
            try:
                self.bot.db.execute(line, True)
            except DBError as db_error:
                if str(db_error).lower() == "no results to fetch":
                    continue

                tmp = f"**l.{index+1}** : {str(db_error)}\n"
                lenTmp = len(tmp)
                if lenTmp + count > 2000:
                    await ctx.respond(msg)
                    count = lenTmp
                    msg = tmp
                else:
                    count += lenTmp
                    msg += tmp

            except Exception as error:
                tmp = f"**l.{index+1}** : Unexcepted error\n"
                lenTmp = len(tmp)
                if lenTmp + count > 2000:
                    await ctx.respond(msg)
                    count = lenTmp
                    msg = tmp
                else:
                    count += lenTmp
                    msg += tmp
                log.writeError(log.formatError(error))
        
        if count > 0:
            await ctx.respond(msg)
        await ctx.respond("Backup execute done !")

    async def lineDisplay(self, ctx: ApplicationContext, filePath: str, limit: int, isError: bool):
        count = 0
        msg = ""

        with open(filePath, "r") as f:
            for line in (f.readlines()[-limit:]):
                newLine = "\n" + log.adjustLog(line, isError)
                lenLine = len(newLine)

                if lenLine + count > 2000:
                    await ctx.respond(f"```{msg}```")
                    count = lenLine
                    msg = str(lenLine)
                else:
                    count += lenLine
                    msg += newLine

        await ctx.respond(f"```{msg}```")

    @josix_slash(description="Display the last logs")
    @option(
        input_type=int,
        name="count",
        description="Number of lines to get",
        default=10
    )
    async def display_logs(self, ctx: ApplicationContext, count: int):
        await ctx.defer(ephemeral=False, invisible=False)
        await self.lineDisplay(ctx, LOG_FILE, count, False)

    @josix_slash(description="Display the last errors")
    @option(
        input_type=int,
        name="count",
        description="Number of lines to get",
        default=10
    )
    async def display_errors(self, ctx: ApplicationContext, count: int):
        await ctx.defer(ephemeral=False, invisible=False)
        await self.lineDisplay(ctx, ERROR_FILE, count, True)

    
    @tasks.loop(hours=24.0)
    async def daily_backup(self):
        if self.startup: # Prevents daily backup on startup
            self.startup = False
            return
        try:
            self.bot.db.backup("", True)
        except Exception as e:
            log.writeError(log.formatError(e))

    @tasks.loop(hours=6.0)
    async def check_connection(self):
        try:
            discord_service.get_user(self.bot.get_handler(), 0)
        except Exception as e:
            if self.report and ((reportChan := self.bot.get_channel(self.report)) or (reportChan := await self.bot.fetch_channel(self.report))):
                await reportChan.send("Connection to database lost !\n" + str(e))
        else:
            log.writeLog("Database connection check passed !")


def setup(bot: Josix):
    bot.add_cog(Owner(bot, True))
