import discord
from discord.ext import commands
from discord import ApplicationContext, option

from database.database import DatabaseHandler
from logwrite import LOG_FILE, ERROR_FILE
from psycopg2 import Error as DBError

import os
import logwrite as log

class Owner(commands.Cog):
    _SCRIPT_DIR = os.path.dirname(__file__)
    _SQL_FILE = os.path.join(_SCRIPT_DIR, '../database/backup.sql')
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

    def cog_check(self, ctx: ApplicationContext):
        return self.bot.is_owner(ctx.author) or ctx.author.guild_permissions.administrator

    @commands.slash_command(description="Stop the bot")
    async def stop_josix(self, ctx: ApplicationContext):
        await ctx.respond("Stopping...")
        await self.bot.close()

    @commands.slash_command(
        description="Create a backup for the databse",
        options=[discord.Option(
            input_type=str,
            name="table",
            description="Name of the table to backup",
            default=""
        )]
    )
    async def backup_database(self, ctx: ApplicationContext, table: str):
        await ctx.defer(ephemeral=False, invisible=False)
        self.db.backup(table)
        await ctx.respond("Backup done !")

    @commands.slash_command(
        description="Execute a query",
        options=[discord.Option(
            input_type=str,
            name="query",
            description="Query to execute",
            required=True
        )]
    )
    async def execute(self, ctx: ApplicationContext, query: str):
        await ctx.defer(ephemeral=False, invisible=False)
        await ctx.respond(self.db.execute(query))

    @commands.slash_command(description="Execute the backup file")
    async def backup_execute(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        res = ""

        with open(Owner._SQL_FILE, 'r') as f:
            lines = f.readlines()
        for index, line in enumerate(lines):
            try:
                self.db.execute(line, True)
            except DBError as db_error:
                res += f"**l.{index+1}** : {str(db_error)}\n"
            except Exception as error:
                res += f"**l.{index+1}** : Unexcepted error\n"
                log.writeError(log.formatError(error))
        
        res += "Backup execute done !"
        await ctx.respond(res)

    @commands.slash_command(description="Display the last logs")
    @option(
        input_type=int,
        name="count",
        description="Number of lines to get",
        default=10
    )
    async def display_logs(self, ctx: ApplicationContext, count: int):
        await ctx.defer(ephemeral=False, invisible=False)
        res = ""
        with open(LOG_FILE, "r") as f:
            for line in (f.readlines()[-count:]):
                res += "\n" + log.adjustLog(line, False)
        await ctx.respond(f"```{res}```")

    @commands.slash_command(description="Display the last errors")
    @option(
        input_type=int,
        name="count",
        description="Number of lines to get",
        default=10
    )
    async def display_errors(self, ctx: ApplicationContext, count: int):
        await ctx.defer(ephemeral=False, invisible=False)
        res = ""
        with open(ERROR_FILE, "r") as f:
            for line in (f.readlines()[-count:]):
                res += "\n" + log.adjustLog(line, True)
        await ctx.respond(f"```{res}```")

    @commands.slash_command(description="test owner")
    async def test_own(self, ctx: ApplicationContext):
        await ctx.respond("All good")


def setup(bot: commands.Bot):
    bot.add_cog(Owner(bot))
