import discord
from discord.ext import commands
from discord import ApplicationContext

from database.database import DatabaseHandler
from logwrite import LOG_FILE, ERROR_FILE, adjustLog

import os

SCRIPT_DIR = os.path.dirname(__file__)
SQL_FILE = os.path.join(SCRIPT_DIR, '../database/backup.sql')

class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()


    @commands.slash_command(description="Stop the bot")
    @commands.is_owner()
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
    @commands.is_owner()
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
    @commands.is_owner()
    async def execute(self, ctx: ApplicationContext, query: str):
        await ctx.defer(ephemeral=False, invisible=False)
        await ctx.respond(self.db.execute(query))

    @commands.slash_command(description="Execute the backup file")
    @commands.is_owner()
    async def backup_execute(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        with open(SQL_FILE, 'r') as f:
            lines = f.readlines()
        for line in lines:
            self.db.execute(line)
        
        await ctx.respond("Backup execute done !")

    @commands.slash_command(description="Display the last logs")
    @commands.is_owner()
    @discord.option(
        input_type=int,
        name="count",
        description="Number of lines to get",
        default=10
    )
    async def display_logs(self, ctx: ApplicationContext, count: int):
        await ctx.defer(ephemeral=False, invisible=False)
        res = ""
        with open(LOG_FILE, "r") as f:
            for line in (f.readlines() [-count:]):
                res += "\n" + adjustLog(line, False)
        await ctx.respond(f"```{res}```")

    @commands.slash_command(description="Display the last errors")
    @commands.is_owner()
    @discord.option(
        input_type=int,
        name="count",
        description="Number of lines to get",
        default=10
    )
    async def display_errors(self, ctx: ApplicationContext, count: int):
        await ctx.defer(ephemeral=False, invisible=False)
        res = ""
        with open(ERROR_FILE, "r") as f:
            for line in (f.readlines() [-count:]):
                res += "\n" + adjustLog(line, True)
        await ctx.respond(f"```{res}```")

def setup(bot: commands.Bot):
    bot.add_cog(Owner(bot))