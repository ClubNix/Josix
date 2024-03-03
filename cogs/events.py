import discord
from discord.ext import commands
from discord.ext.commands import BotMissingPermissions, MissingPermissions, MissingRequiredArgument, NoPrivateMessage, \
    CommandOnCooldown, NotOwner
from discord import RawThreadUpdateEvent, ApplicationContext, DiscordException, NotFound, Forbidden, CheckFailure
from discord.utils import get as discordGet

import logwrite as log
import os
import json

from json import JSONDecodeError
from josix import Josix
from bot_utils import JosixCog
from database.services import discord_service

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
    _FILE_PATH = os.path.join(_SCRIPT_DIR, '../config.json')

    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot
        self.close = ""
        self.open = ""

        try:
            with open(Events._FILE_PATH, "r") as f:
                data = json.load(f)

            self.close = data["tags"]["closed"]
            self.open = data["tags"]["open"]
        except (JSONDecodeError, FileNotFoundError, KeyError):
            pass

    @staticmethod
    async def getTags(thread: discord.Thread, close: str, open: str) -> tuple[discord.ForumTag, discord.ForumTag | None] | None:
        cTag: discord.ForumTag | None = None
        oTag: discord.ForumTag | None = None

        if not isinstance(thread.parent, discord.ForumChannel):
            return None

        if close != "":
            cTag = discordGet(thread.parent.available_tags, name=close)

        if open != "":
            oTag = discordGet(thread.parent.available_tags, name=open)

        newTags = thread.parent.available_tags.copy()
        if not cTag:
            cTag = discord.ForumTag(name=close, emoji="🔴")
            newTags.append(cTag)
        if not oTag:
            oTag = discord.ForumTag(name=open, emoji="🟢")
            newTags.append(oTag)

        if len(newTags) > len(thread.parent.available_tags):
            await thread.parent.edit(available_tags=newTags)

        return (cTag, oTag)

# ==================================================
# ==================================================
# ==================================================

    @commands.Cog.listener()
    async def on_ready(self):
        log.writeLog(f"==> Bot ready : py-cord v{discord.__version__}\n")

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if not isinstance(thread.parent, discord.ForumChannel): return

        try:
            await thread.send("This thread is now open. You can close it automatically by using `/close`")
        except Exception as e:
            log.writeError(log.formatError(e))

        result = await Events.getTags(thread, self.close, self.open)
        if result is None or result[1] is None:
            return
        
        _, oTag = result
        if oTag and oTag not in thread.applied_tags:
            tags = thread.applied_tags.copy()
            if not tags:
                tags = [oTag]
            else:
                tags.append(oTag)

            await thread.edit(applied_tags=tags)

    @commands.Cog.listener()
    async def on_raw_thread_update(self, payload: RawThreadUpdateEvent):
        if not (guild := self.bot.get_guild(payload.guild_id)) or not (guild := await self.bot.fetch_guild(payload.guild_id)):
            return

        if not payload.thread:
            thread = guild.get_thread(payload.thread_id)
            if not thread:
                return
        else:
            thread = payload.thread

        if not isinstance(thread.parent, discord.ForumChannel):
            return

        data = payload.data
        result = await Events.getTags(thread, self.close, self.open)
        if result is None or None in result:
            return

        cTag, oTag = result
        tags = thread.applied_tags.copy()
        if data["thread_metadata"]["archived"] and data["thread_metadata"]["locked"]:
            # You can't edit archived thread and this current method creates useless loop
            """
            try:
                if oTag:
                    try:
                        del tags[tags.index(oTag)]
                    except (ValueError, IndexError):
                        pass

                if cTag and not cTag in tags:
                    tags.append(cTag)
                    await thread.unarchive()
                    await thread.edit(applied_tags=tags)
                    await thread.archive()
            except Exception as e:
                log.writeError(log.formatError(e))
            """

        elif not data["thread_metadata"]["archived"]:
            try:
                if cTag:
                    try:
                        del tags[tags.index(cTag)]
                    except (ValueError, IndexError):
                        pass

                if oTag and not oTag in tags:
                    tags.append(oTag)
                    await thread.edit(applied_tags=tags)
            except Exception as e:
                log.writeError(log.formatError(e))

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
