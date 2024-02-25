import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option
from discord import NotFound, InvalidArgument, HTTPException

import re
import logwrite as log

from josix import Josix
from cogs.logger import LoggerView
from bot_utils import JosixCog, josix_slash
from database.services import (
    logger_service,
    reactrole_service,
    discord_service,
    guild_service,
)


class Admin(JosixCog):
    """
    Represents the admin commands extension of the bot

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    """

    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot


    @josix_slash(description="Clear messages from the channel")
    @discord.default_permissions(manage_messages=True)
    @commands.guild_only()
    @option(
        input_type=int,
        name="limit",
        description="Limit of messages to delete (default 10, can't be more than 50)",
        default=10,
        min_value=1,
        max_value=50
    )
    async def clear(self, ctx: ApplicationContext, limit: int):
        await ctx.channel.purge(limit=limit)
        await ctx.delete()


    @josix_slash(description="Add a couple of reaction-role to the message")
    @discord.default_permissions(manage_messages=True)
    @commands.guild_only()
    @option(
        input_type=str,
        name="msg_id",
        description="ID of the message you want to add the couple",
        required=True
    )
    @option(
        input_type=str,
        name="emoji",
        description="Emoji of the couple (no custom)",
        required=True
    )
    @option(
        input_type=discord.Role,
        name="role",
        description="Mention of the role of the couple",
        required=True
    )
    async def add_couple(self, ctx: ApplicationContext, msg_id: str, emoji: str, role: discord.Role):
        await ctx.defer(ephemeral=False, invisible=False)

        idRole = role.id
        idMsg = 0
        new = False
        testEmj = None
        testMsg = None
        testGuild = None
        duos = None
        msg: discord.Message = None
        handler = self.bot.get_handler()

        testEmj = re.compile("[<>:]")
        if testEmj.match(emoji):
            await ctx.respond("You can't use a custom emoji")
            return

        try:
            idMsg = int(msg_id)
        except ValueError:
            await ctx.respond("Incorrect value given for the message_id parameter")
            return

        msg = await ctx.channel.fetch_message(idMsg) # TODO : Catch Unknown message
        if not msg:
            await ctx.respond("Unknown message")
            return

        try:
            await msg.add_reaction(emoji)
        except (NotFound, InvalidArgument, HTTPException):
            await ctx.respond("Unknown error with the emoji")
            return

        try:
            testGuild = discord_service.get_guild(handler, ctx.guild_id)
            if not testGuild:
                discord_service.add_guild(handler, ctx.guild_id, ctx.channel_id)

            testMsg = reactrole_service.get_reaction_message(handler, idMsg)
            if not testMsg:
                reactrole_service.add_message_react(handler, ctx.guild_id, idMsg)
                new = True
        except Exception as e:
            await msg.clear_reaction(emoji)
            log.writeError(str(e))

        duos = reactrole_service.get_couples(handler, idMsg)
        if duos:
            for duo in duos:
                if emoji == duo.emoji:
                    await ctx.respond("The emoji is already used in the message")
                    if new:
                        reactrole_service.delete_message_react(handler, idMsg)
                    return

                elif idRole == duo.idRole:
                    await ctx.respond("The role is already used in the message")
                    await msg.clear_reaction(emoji)
                    if new:
                        reactrole_service.delete_message_react(handler, idMsg)
                    return

        reactrole_service.add_couple(handler, (emoji, idRole), idMsg)
        await ctx.respond("Done !", delete_after=5.0)


    @josix_slash(description="Delete a couple in a reaction-role message")
    @discord.default_permissions(manage_messages=True)
    @commands.guild_only()
    @option(
        input_type=str,
        name="msg_id",
        description="ID of the message you want to add the couple",
        required=True
    )
    @option(
        input_type=str,
        name="emoji",
        description="Emoji of the couple (no custom)",
        required=True
    )
    @option(
        input_type=discord.Role,
        name="role",
        description="Mention of the role of the couple",
        required=True
    )
    async def delete_couple(self, ctx: ApplicationContext, msg_id: str, emoji: str, role: discord.Role):
        testMsg = await ctx.respond("Testing...")
        og: discord.InteractionMessage = await testMsg.original_response()

        idRole = role.id
        idMsg = 0
        testEmj = None
        duos = None
        msg: discord.Message = None
        idCouple = 0
        handler = self.bot.get_handler()

        testEmj = re.compile("[<>:]")
        if testEmj.match(emoji):
            await og.edit(content="❌ You can't use a custom emoji")
            return

        try:
            idMsg = int(msg_id)
        except ValueError:
            await og.edit(content="❌ Incorrect value given for the message_id parameter")
            return

        msg = await ctx.channel.fetch_message(idMsg)
        if not msg:
            await og.edit(content="❌ Unknown message")
            return

        try:
            await og.add_reaction(emoji)
        except (NotFound, InvalidArgument, HTTPException):
            await og.edit(content="❌ Unknown error with the emoji")
            return

        if not (discord_service.get_guild(handler, ctx.guild_id) and reactrole_service.get_reaction_message(handler, idMsg)):
            await og.edit(content="❌ This message is unregistered")
            return

        duos = reactrole_service.get_couples(handler, idMsg)
        test = False
        for duo in duos:
            if duo.emoji == emoji and duo.idRole == idRole:
                idCouple = duo.id
                test = True
                break
        
        if test:
            reactrole_service.delete_message_couple(handler, idMsg, idCouple)
            await og.edit(content="✅ Done !")
            await msg.clear_reaction(emoji)
            await testMsg.delete_original_response()
        else:
            await og.edit(content="❌ Unknow couple")


    @josix_slash(description="Set this channel as an announcement channel for the bot")
    @discord.default_permissions(manage_channels=True)
    @commands.guild_only()
    async def set_news_channel(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        handler = self.bot.get_handler()
        testGuild = None
        idGuild = ctx.guild_id
        idChan = ctx.channel_id

        testGuild = discord_service.get_guild(handler, idGuild)
        if not testGuild:
            discord_service.add_guild(handler, idGuild, idChan)
        else:
            guild_service.update_news_channel(handler, idGuild, idChan)
        await ctx.respond("this channel will now host my news !")

    @josix_slash(description="Set current channel as the XP annouce channel (can be the same as the news channel)")
    @discord.default_permissions(manage_channels=True)
    @commands.guild_only()
    async def set_xp_channel(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        handler = self.bot.get_handler()
        testGuild = None
        idGuild = ctx.guild_id
        idChan = ctx.channel_id

        testGuild = discord_service.get_guild(handler, idGuild)
        if not testGuild:
            discord_service.add_guild(handler, idGuild, idChan)
        else:
            self.bot.db.changeXPChan(idGuild, idChan)
        await ctx.respond("this channel will now the XP news !")


    @josix_slash(description="Enable or disable the xp system on the server")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    async def enable_xp_system(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        handler = self.bot.get_handler()
        xpState = None
        idGuild = ctx.guild_id

        xpState = discord_service.get_guild(handler, idGuild)
        if not xpState:
            discord_service.add_guild(handler, idGuild)
            xpState = discord_service.get_guild(handler, idGuild)

        enabled = xpState.enableXp
        self.bot.db.updateGuildXpEnabled(idGuild)
        await ctx.respond(f"The system XP for this server has been set to **{not enabled}**")


    @josix_slash(description="Create a new XP season in the server (store rankings and reset everyone)")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=str,
        name="label",
        description="Label of the ended season (default : current index)",
        default=None
    )
    async def create_new_season(self, ctx: ApplicationContext, label: str):
        await ctx.defer(ephemeral=False, invisible=False)

        if label is None:
            label = ""

        guild = ctx.guild
        if not guild:
            await ctx.respond("Data not found")
            return

        id_season = -1
        try:
            id_season = self.bot.db.storeSeason(guild.id, label)
        except ValueError as e:
            await ctx.respond(e)
            return

        self.bot.db.storeScores(guild.id, id_season)
        self.bot.db.cleanXPGuild(guild.id)
        await ctx.respond("A new season has been started !")


    @josix_slash(description="Delete a season from history")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=str,
        name="label",
        description="label of targeted season"
    )
    async def delete_season(self, ctx: ApplicationContext, label: str):
        await ctx.defer(ephemeral=False, invisible=False)

        guild = ctx.guild
        if not guild:
            await ctx.respond("Data not found")
            return

        if not (season := self.bot.db.getSeasonByLabel(guild.id, label)):
            await ctx.respond("Unknown season, make sure you entered the right label")
            return

        self.bot.db.deleteSeason(season)
        await ctx.respond("Done !")


    @josix_slash(description="Update season name")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=str,
        name="old_label",
        description="Old label of the targeted season"
    )
    @option(
        input_type=str,
        name="new_label",
        description="New label of the season"
    )
    async def update_season(self, ctx: ApplicationContext, old_label: str, new_label: str):
        await ctx.defer(ephemeral=False, invisible=False)

        guild = ctx.guild
        if not guild:
            await ctx.respond("Data not found")
            return

        if not (season := self.bot.db.getSeasonByLabel(guild.id, old_label)):
            await ctx.respond("Unknown season, make sure you entered the right label")
            return

        if self.bot.db.getSeasonByLabel(guild.id, new_label):
            await ctx.respond(f"The label '{new_label}' is already used in a season for this server")
            return

        self.bot.db.updateSeasonLabel(season, new_label)
        await ctx.respond("Done !")


    @josix_slash(description="Set up the custom welcome system for your server")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=discord.TextChannel,
        name="channel",
        description="Channel that will host the welcome message",
        default=None
    )
    @option(
        input_type=discord.Role,
        name="role",
        description="Role that will be automatically given",
        default=None
    )
    @option(
        input_type=str,
        name="message",
        description="Custom welcoming message",
        default="Welcome {user}"
    )
    @option(
        input_type=bool,
        name="keep",
        description="Keep old parameters if not set",
        default=True
    )
    async def set_custom_welcome(self, ctx: ApplicationContext, channel: discord.TextChannel, role: discord.Role, message: str, keep: bool):
        await ctx.defer(ephemeral=False, invisible=False)
        if not (channel or role or message):
            await ctx.respond("Can't set up your custom welcome")
            return

        if len(message) > 512:
            await ctx.respond("The message is too long")
            return

        idGuild = ctx.guild_id
        handler = self.bot.get_handler()
        dbGuild = discord_service.get_guild(handler, idGuild)

        if not dbGuild:
            discord_service.add_guild(handler, idGuild)
            dbGuild = discord_service.get_guild(handler, idGuild)

        if not channel:
            idChan = dbGuild.wChan if keep else 0
        else:
            idChan = channel.id
        if not role:
            idRole = dbGuild.wRole if keep else 0
        else:
            idRole = role.id
        if not message:
            message = dbGuild.wText if keep else ""

        self.bot.db.updateWelcomeGuild(idGuild, idChan, idRole, message)
        await ctx.respond("Your custome welcome message has been set")


    @josix_slash(description="Enable or disable the welcome system")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    async def enable_welcome(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        idGuild = ctx.guild_id
        handler = self.bot.get_handler()
        dbGuild = discord_service.get_guild(handler, idGuild)

        if not dbGuild:
            discord_service.add_guild(handler, idGuild)
            dbGuild = discord_service.get_guild(idGuild)

        enabled = dbGuild.enableWelcome
        self.bot.db.updateGuildWelcomeEnabled(idGuild)
        await ctx.respond(f"The custom welcome system for this server has been set to **{not enabled}**")


    @josix_slash(description="Choose which logs to register")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=bool,
        name="keep",
        description="Keep old selected logs if not set"
    )
    async def set_logger(self, ctx: ApplicationContext, keep: bool):
        await ctx.respond("Choose your logs :", view=LoggerView(self.bot.db, keep))


    @josix_slash(description="Choose where to send the logs")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=discord.TextChannel,
        name="channel",
        description="The channel that will host the bot registered logs",
        default=None
    )
    async def set_log_channel(self, ctx: ApplicationContext, channel: discord.TextChannel):
        await ctx.defer(ephemeral=False, invisible=False)
        handler = self.bot.get_handler()
        if channel:
            logger_service.update_log_channel(handler, ctx.guild.id, channel.id)
            await ctx.respond("Logs channel set")
        else:
            logger_service.update_log_channel(handler, ctx.guild.id, None)
            await ctx.respond("Logs channel unset")


    @josix_slash(description="Block or unblock a category from xp leveling")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=discord.CategoryChannel,
        name="category",
        description="The category to block or unblock",
        required=True
    )
    async def block_category(self, ctx: ApplicationContext, category: discord.CategoryChannel):
        await ctx.defer(ephemeral=False, invisible=False)

        handler = self.bot.get_handler()
        idCat = category.id
        idGuild = ctx.guild_id
        dbGuild = discord_service.get_guild(handler, idGuild)

        if not dbGuild:
            discord_service.add_guild(handler, idGuild)
            dbGuild = discord_service.get_guild(idGuild)

        if idCat in dbGuild.blockedCat:
            self.bot.db.unblockCategory(idCat, idGuild)
            text = "unblocked"
        else:
            self.bot.db.blockCategory(idCat, idGuild)
            text = "blocked"
        await ctx.respond(f"The category **{category.name}** is now **{text}**")


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot, True))
