import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option
from discord import NotFound, InvalidArgument, HTTPException

import re
import logwrite as log
import os

from database.database import DatabaseHandler
from cogs.logger import LoggerView
from bot_utils import josix_slash


class Admin(commands.Cog):
    """
    Represents the admin commands extension of the bot

    Attributes
    ----------
    bot : discord.ext.commands.Bot
        The bot that loaded this extension
    db : DatabaseHandler
        A handler to perform requests on the database
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

    @josix_slash(description="Clear messages from the channel")
    @commands.has_permissions(manage_messages=True)
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
        await ctx.defer(ephemeral=False, invisible=False)
        await ctx.channel.purge(limit=limit)
        await ctx.respond("Done !", delete_after=5.0)

    @josix_slash(description="Add a couple of reaction-role to the message")
    @commands.has_permissions(manage_messages=True)
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

        testEmj = re.compile("[<>:]")
        if testEmj.match(emoji):
            await ctx.respond("You can't use a custom emoji")
            return

        try:
            idMsg = int(msg_id)
        except ValueError:
            await ctx.respond("Incorrect value given for the message_id parameter")
            return

        msg = await ctx.channel.fetch_message(idMsg)
        if not msg:
            await ctx.respond("Unknown message")
            return

        try:
            await msg.add_reaction(emoji)
        except (NotFound, InvalidArgument, HTTPException):
            await ctx.respond("Unknown error with the emoji")
            return

        try:
            testGuild = self.db.getGuild(ctx.guild_id)
            if not testGuild:
                self.db.addGuild(ctx.guild_id, ctx.channel_id)

            testMsg = self.db.getMsg(idMsg)
            if not testMsg:
                self.db.addMsg(ctx.guild_id, idMsg)
                new = True
        except Exception as e:
            await msg.clear_reaction(emoji)
            log.writeError(str(e))

        duos = self.db.getCouples(idMsg)
        if duos:
            for duo in duos:
                if emoji == duo.emoji:
                    await ctx.respond("The emoji is already used in the message")
                    if new:
                        self.db.delMessageReact(idMsg)
                    return

                elif idRole == duo.idRole:
                    await ctx.respond("The role is already used in the message")
                    await msg.clear_reaction(emoji)
                    if new:
                        self.db.delMessageReact(idMsg)
                    return

        self.db.addCouple((emoji, idRole), idMsg)
        await ctx.respond("Done !", delete_after=5.0)

    @josix_slash(description="Delete a couple in a reaction-role message")
    @commands.has_permissions(manage_messages=True)
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

        if not (self.db.getGuild(ctx.guild_id) and self.db.getMsg(idMsg)):
            await og.edit(content="❌ This message is unregistered")
            return

        duos = self.db.getCouples(idMsg)
        test = False
        for duo in duos:
            if duo.emoji == emoji and duo.idRole == idRole:
                idCouple = duo.id
                test = True
                break
        
        if test:
            self.db.delMessageCouple(idMsg, idCouple)
            await og.edit(content="✅ Done !")
            await msg.clear_reaction(emoji)
        else:
            await og.edit(content="❌ Unknow couple")

    @josix_slash(description="Set this channel as an announcement channel for the bot")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def set_news_channel(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        
        testGuild = None
        idGuild = ctx.guild_id
        idChan = ctx.channel_id

        testGuild = self.db.getGuild(idGuild)
        if not testGuild:
            self.db.addGuild(idGuild, idChan)
        else:
            self.db.changeNewsChan(idGuild, idChan)
        await ctx.respond("this channel will now host my news !")

    @josix_slash(description="Set current channel as the XP annouce channel (can be the same as the news channel)")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def set_xp_channel(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        testGuild = None
        idGuild = ctx.guild_id
        idChan = ctx.channel_id

        testGuild = self.db.getGuild(idGuild)
        if not testGuild:
            self.db.addGuild(idGuild, idChan)
        else:
            self.db.changeXPChan(idGuild, idChan)
        await ctx.respond("this channel will now the XP news !")


    @josix_slash(description="Enable or disable the xp system on the server")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def enable_xp_system(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        xpState = None
        idGuild = ctx.guild_id

        xpState = self.db.getGuild(idGuild)
        if not xpState:
            self.db.addGuild(idGuild)
            xpState = self.db.getGuild(idGuild)

        enabled = xpState.enableXp
        self.db.updateGuildXpEnabled(idGuild)
        await ctx.respond(f"The system XP for this server has been set to **{not enabled}**")

    @josix_slash(description="Set up the custom welcome system for your server")
    @commands.has_permissions(manage_guild=True)
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
        default=""
    )
    @option(
        input_type=bool,
        name="keep",
        description="Keep old parameters if not set",
        default=True
    )
    async def set_custom_welcome(self, ctx: ApplicationContext, channel: discord.TextChannel, role: discord.Role, message: str, keep: bool):
        if not (channel or role or message):
            await ctx.respond("Can't set up your custom welcome")
            return

        if len(message) > 512:
            await ctx.respond("The message is too long")
            return

        await ctx.defer(ephemeral=False, invisible=False)
        idGuild = ctx.guild_id
        dbGuild = self.db.getGuild(idGuild)

        if not dbGuild:
            self.db.addGuild(idGuild)
            dbGuild = self.db.getGuild(idGuild)

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

        self.db.updateWelcomeGuild(idGuild, idChan, idRole, message)
        await ctx.respond("Your custome welcome message has been set")


    @josix_slash(description="Enable or disable the welcome system")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def enable_welcome(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        idGuild = ctx.guild_id
        dbGuild = self.db.getGuild(idGuild)
        if not dbGuild:
            self.db.addGuild(idGuild)
            dbGuild = self.db.getGuild(idGuild)

        enabled = dbGuild.enableWelcome
        self.db.updateGuildWelcomeEnabled(idGuild)
        await ctx.respond(f"The custom welcome system for this server has been set to **{not enabled}**")

    @josix_slash(description="Choose which logs to register")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=bool,
        name="keep",
        description="Keep old selected logs if not set"
    )
    async def set_logger(self, ctx: ApplicationContext, keep: bool):
        await ctx.respond("Choose your logs :", view=LoggerView(self.db, keep))

    @josix_slash(description="Choose where to send the logs")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=discord.TextChannel,
        name="channel",
        description="The channel that will host the bot registered logs",
        default=None
    )
    async def set_log_channel(self, ctx: ApplicationContext, channel: discord.TextChannel):
        if channel:     
            self.db.updateLogChannel(ctx.guild.id, channel.id)
            await ctx.respond("Logs channel set")
        else:
            self.db.updateLogChannel(ctx.guild.id, None)
            await ctx.respond("Logs channel unset")


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
