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


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

    @commands.slash_command(description="Clear messages from the channel")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @option(
        input_type=int,
        name="limit",
        description="Limit of messages to delete (default 10, can't be more than 50)",
        default=10,
        min_value=0,
        max_value=50
    )
    async def clear(self, ctx: ApplicationContext, limit: int):
        await ctx.defer(ephemeral=False, invisible=False)
        await ctx.channel.purge(limit=limit)
        await ctx.respond("Done !", delete_after=5.0)

    @commands.slash_command(description="Add a couple of reaction-role to the message")
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

        roleId = role.id
        msgId = 0
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
            msgId = int(msg_id)
        except ValueError:
            await ctx.respond("Incorrect value given for the message_id parameter")
            return

        msg = await ctx.channel.fetch_message(msgId)
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

            testMsg = self.db.getMsg(msgId)
            if not testMsg:
                self.db.addMsg(ctx.guild_id, msgId)
                new = True
        except Exception as e:
            await msg.clear_reaction(emoji)
            log.writeError(str(e))

        duos = self.db.getCouples(msgId)
        for duo in duos:
            if emoji == duo[0]:
                await ctx.respond("The emoji is already used in the message")
                if new:
                    self.db.delMessageReact(msgId)
                return

            elif roleId == duo[1]:
                await ctx.respond("The role is already used in the message")
                await msg.clear_reaction(emoji)
                if new:
                    self.db.delMessageReact(msgId)
                return

        self.db.addCouple((emoji, roleId), msgId)
        await ctx.respond("Done !", delete_after=5.0)

    @commands.slash_command(description="Set this channel as an announcement channel for the bot")
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

    @commands.slash_command(description="Set current channel as the XP annouce channel (can be the same as the news channel)")
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


    @commands.slash_command(description="Enable or disable the xp system on the server")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def enable_xp_system(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        xpState = None
        idGuild = ctx.guild_id

        xpState = self.db.getGuildXP(idGuild)
        if not xpState:
            self.db.addGuild(idGuild)
            xpState = self.db.getGuildXP(idGuild)

        enabled = xpState[1]
        self.db.updateGuildXpEnabled(idGuild)
        await ctx.respond(f"The system XP for this server has been set to **{not enabled}**")

    @commands.slash_command(description="Set up the custom welcome system for your server")
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
    async def set_custom_welcome(self, ctx: ApplicationContext, channel: discord.TextChannel, role: discord.Role, message: str):
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

        idChan = channel.id if channel else None
        idRole = role.id if role else None
        self.db.updateWelcomeGuild(idGuild, idChan, idRole, message)
        await ctx.respond("Your custome welcome message has been set")


    @commands.slash_command(description="Enable or disable the welcome system")
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

    @commands.slash_command(description="Choose which logs to register")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def set_logger(self, ctx: ApplicationContext):
        await ctx.respond("Choose your logs :", view=LoggerView(self.db))

    @commands.slash_command(description="Choose where to send the logs")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @option(
        input_type=discord.TextChannel,
        name="channel",
        description="The channel that will host the bot registered logs",
        default=None
    )
    async def set_log_channel(self, ctx: ApplicationContext, channel: discord.TextChannel):
        if not channel:
            # delete the column value to stop the logs
            pass
        else:
            # update
            pass

        await ctx.respond("WIP")


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
