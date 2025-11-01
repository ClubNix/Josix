import os

import discord
from discord import (
    ApplicationContext,
    CheckFailure,
    DiscordException,
    Forbidden,
    NotFound,
)
from discord.ext import commands
from discord.ext.commands import (
    BotMissingPermissions,
    CommandOnCooldown,
    MissingPermissions,
    MissingRequiredArgument,
    NoPrivateMessage,
    NotOwner,
)

import pkg.logwrite as log
from database.services import discord_service
from josix import Josix
from pkg.bot_utils import JosixCog


class Events(JosixCog):
    """
    Represents the extension for all the events that can't be used
    in specific extensions

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    close : str
        Close tag name
    open : str
        Open tag name
    """
    
    _SCRIPT_DIR = os.path.dirname(__file__)
    _FILE_PATH = os.path.join(_SCRIPT_DIR, '../configs/config.json')

    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot

# ==================================================
# ==================================================
# ==================================================

    @commands.Cog.listener()
    async def on_ready(self):
        log.writeLog(f"==> Bot ready : py-cord v{discord.__version__}\n")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        handler = self.bot.get_handler()
        dbGuild = discord_service.get_guild(handler, member.guild.id)
        if not dbGuild:
            return

        if not dbGuild.enableWelcome:
            return

        chan = member.guild.get_channel(dbGuild.wChan)
        role = member.guild.get_role(dbGuild.wRole)
        text = dbGuild.wText

        if isinstance(chan, (
            discord.StageChannel,
            discord.ForumChannel,
            discord.CategoryChannel
        )):
            return
        
        if role:
            await member.add_roles(role, reason="Welcome role")
        
        if chan:
            if text:
                text = text.format(
                    user=member.mention,
                    server=member.guild.name,
                    ln="\n"
                )
            else:
                text = f"Welcome on the server **{member.guild.name}** {member.mention}"
            await chan.send(text)

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: ApplicationContext, error: DiscordException):
        if isinstance(error, Forbidden):
            await ctx.respond("Ho no i can't do something :(")
        elif isinstance(error, NotFound):
            await ctx.respond("Bip Boup **Error 404**")
        elif isinstance(error, BotMissingPermissions):
            await ctx.respond("HEY ! Gimme more permissions...")
        elif isinstance(error, MissingPermissions):
            await ctx.respond("Sorry but you lack permissions (skill issue)")
        elif isinstance(error, MissingRequiredArgument):
            await ctx.respond("An argument is missing in your command (skill issue n°2)")
        elif isinstance(error, NoPrivateMessage):
            await ctx.respond("This command can only be used in a server (get some friends)")
        elif isinstance(error, CheckFailure):
            await ctx.respond("You didn't match the command checks")
        elif isinstance(error, CommandOnCooldown):
            cooldown_error: CommandOnCooldown = error
            await ctx.respond(f"Too fast bro, wait {round(cooldown_error.retry_after, 2)} seconds to retry this command")
        elif isinstance(error, NotOwner):
            await ctx.respond("This command is only for my master ! (skill issue n°3)")
        else:
            await ctx.respond("Unknown error occured")
            log.writeError(log.formatError(error))
        

def setup(bot: Josix):
    bot.add_cog(Events(bot, False))
