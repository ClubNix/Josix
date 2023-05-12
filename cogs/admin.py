import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option
from discord import NotFound, InvalidArgument, HTTPException

import re
import logwrite as log
import os

from database.database import DatabaseHandler


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
        default=10
    )
    async def clear(self, ctx: ApplicationContext, limit: int):
        await ctx.defer(ephemeral=False, invisible=False)
        if limit < 0 or 50 < limit:
            limit = 10 
        await ctx.channel.purge(limit=limit)
        await ctx.respond("Done !")

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
            if testGuild is None or len(testGuild) == 0:
                self.db.addGuild(ctx.guild_id, ctx.channel_id)

            testMsg = self.db.getMsg(msgId)
            if testMsg is None or len(testMsg) == 0:
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
        if not testGuild or len(testGuild) == 0:
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
        if not testGuild or len(testGuild) == 0:
            self.db.addGuild(idGuild, idChan)
        else:
            self.db.changeXPChan(idGuild, idChan)
        await ctx.respond("this channel will now host my the news about XP change !")


    @commands.slash_command(description="Enable or disable the xp system on the server")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def enable_xp_system(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)

        xpState = None
        idGuild = ctx.guild_id

        xpState = self.db.getGuildXP(idGuild)
        if not xpState or len(xpState) == 0:
            self.db.addGuild(idGuild)
            xpState = self.db.getGuildXP(idGuild)

        enabled: bool = xpState[1]
        self.db.updateGuildXpEnabled(idGuild)
        await ctx.respond(f"The system XP for this server has been set to **{not enabled}**")


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
