import discord
from discord.ext import commands
from discord import ApplicationContext

from database.database import DatabaseHandler

import os

SCRIPT_DIR = os.path.dirname(__file__)
FILE_PATH = os.path.join(SCRIPT_DIR, '../database/backup.sql')

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

        with open(FILE_PATH, 'r') as f:
            lines = f.readlines()
        for line in lines:
            self.db.execute(line)
        
        await ctx.respond("Backup execute done !")


def setup(bot: commands.Bot):
    bot.add_cog(Owner(bot))