import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option
from discord import NotFound, InvalidArgument, HTTPException

import asyncio
import re
import logwrite as log
import os

from database.database import DatabaseHandler


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

    async def createCouple(self, ctx: ApplicationContext, duos: list) -> tuple:
        chan = ctx.channel

        msg = "For the first part, react to this message with the emoji you want to add in the reaction role!\nError : "
        error = "None"
        config = await chan.send("Go !")

        def checkReact(reaction: discord.Reaction, user: discord.User):
            return ctx.author.id == user.id and config.id == reaction.message.id

        def checkRole(message: discord.Message):
            return message.author.id == ctx.author.id and config.channel.id == message.channel.id

        test = False
        count = 0
        while not test:
            if count >= 3:  # The user can fails 3 times before the end of the command
                await config.delete()
                await chan.send("Too many fails, retry please")
                return None

            test = True

            # Displaying the configuration messages
            await config.edit(msg + error)
            await config.clear_reactions()

            try:    
                reaction, _ = await self.bot.wait_for('reaction_add', check=checkReact, timeout=60)
                reactName = reaction.emoji

                if reaction.is_custom_emoji():
                    test = False
                    error = "Custom emojis are not allowed"
                    count += 1
                    continue

                for duo in duos:
                    if reactName == duo[0]:
                        test = False
                        error = "This emoji is already linked to a role in this reaction role message"
                        count += 1
                if not test:
                    continue

            except asyncio.TimeoutError as _:
                test = False
                error = "You've been too long to answer, retry"
                count += 1
                continue

            await config.edit("Now mention the role which will be linked to the reaction or type its id :")
            try:    
                answer = await self.bot.wait_for('message', check=checkRole, timeout=60)
                mentions = answer.role_mentions  # all the mentions of a role in the message
                await answer.delete()

                if len(mentions) > 0:
                    role = mentions[0]  # Take the first mention in the message
                else:
                    try:
                        role = ctx.guild.get_role(int(answer.content))
                        if role is None:
                            test = False
                            error = "Unknown role"
                            count += 1
                            continue

                    except ValueError as _:
                        test = False
                        error = "Wrong role ID given"
                        count += 1
                        continue
                
            except asyncio.TimeoutError as _:
                test = False
                error = "You've been too long too answer"
                count += 1
                continue

            for duo in duos:
                if role.id == duo[1]:
                    test = False
                    error = "This role is already linked to an emoji in this reaction role message"
                    count += 1

        await config.delete()
        return (reaction, role.id)

    @commands.slash_command(description="Set the message as a reaction role message")
    @commands.guild_only()
    @option(
        input_type=str,
        name="message_id",
        description="ID of the message to which you want to add a reaction-role",
        required=True
    )
    async def create_react_role(self, ctx: ApplicationContext, message_id: str):
        try:
            msg_id = int(message_id)
        except ValueError as _:
            ctx.respond("Wrong value")
            return

        msg = await ctx.channel.fetch_message(msg_id)
        if msg is None:
            await ctx.respond("Wrong ID given for the message or not in this channel")
            return

        testGuild = self.db.getGuild(ctx.guild_id)
        if testGuild is None or len(testGuild) == 0:
            self.db.addGuild(ctx.guild_id, ctx.channel_id)

        testMsg = self.db.getMsg(msg_id)
        if testMsg is None or len(testMsg) == 0:
            self.db.addMsg(ctx.guild_id, msg_id)

        res = await ctx.respond("Launching reaction role creation...")

        duos = self.db.getCouples(msg_id)
        couple = await self.createCouple(ctx, duos)
        if couple is None:
            return

        self.db.addCouple(couple, msg_id)
        await msg.add_reaction(couple[0])
        await res.edit_original_response(content="Done !")

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
                    self.db.delMsg(msgId)
                return

            elif roleId == duo[1]:
                await ctx.respond("The role is already used in the message")
                await msg.clear_reaction(emoji)
                if new:
                    self.db.delMsg(msgId)
                return

        self.db.addCouple((emoji, roleId), msgId)
        await ctx.respond("Done !")

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
