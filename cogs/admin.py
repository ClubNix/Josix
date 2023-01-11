import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option
from discord import NotFound, InvalidArgument

import asyncio
import re

from database.database import DatabaseHandler

EMOJI_PATTERN = re.compile(
    "(["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "])"
)

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()

    async def createCouple(self, ctx: ApplicationContext, duos: list) -> tuple:
        chan = ctx.channel

        msg = "For the first part, react to this message with the emoji you want to add in the reaction role !\nError : "
        error = "None"
        config = await chan.send("Go !")

        def checkReact(reaction: discord.Reaction, user: discord.User):
            return ctx.author.id == user.id and config.id == reaction.message.id

        def checkRole(message: discord.Message):
            return message.author.id == ctx.author.id and config.channel.id == message.channel.id

        test = False
        count = 0
        while not test:
            if count >= 3: # The user can fails 3 times before the end of the command
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
                mentions = answer.role_mentions # all the mentions of a role in the message
                await answer.delete()

                if len(mentions) > 0:
                    role = mentions[0] # Take the first mention in the message
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
    @option(
        input_type=str,
        name="message_id",
        description="ID of the message to which you want to add a reaction-role",
        required=True
    )
    async def create_react_role(self, ctx: ApplicationContext, id: str):
        try:
            msg_id = int(id)
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
    @option(
        input_type=int,
        name="limit",
        description="Limit of messages to delete (default 10, can't be more than 50)",
        default=10
    )
    async def clear(self, ctx: ApplicationContext, limit: int):
        if limit < 0 or 50 < limit:
            limit = 10 
        await ctx.channel.purge(limit=limit)
        await ctx.respond("Done !")

    @commands.slash_command(description="Add a couple of reaction-role to the message")
    @commands.has_permissions(manage_messages=True)
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
    async def add_couple(self, ctx: ApplicationContext, msg_p: str, emoji: str, role: discord.Role):
        values = EMOJI_PATTERN.search(emoji)
        roleId = role.id
        msgId = 0
        new = False
        emjName = ""
        testMsg = None
        testGuild = None
        duos = None
        msg: discord.Message = None

        if not values:
            ctx.respond("Wrong emoji given")
            return
        else:
            emjName = values.group(0)

        try:
            msgId = int(msg_p)
        except ValueError:
            await ctx.respond("Incorrect value given for the message_id parameter")
            return

        msg = await ctx.channel.fetch_message(msgId)
        if not msg:
            await ctx.respond("Unknown message")
            return

        testGuild = self.db.getGuild(ctx.guild_id)
        if testGuild is None or len(testGuild) == 0:
            self.db.addGuild(ctx.guild_id, ctx.channel_id)

        testMsg = self.db.getMsg(msgId)
        if testMsg is None or len(testMsg) == 0:
            self.db.addMsg(ctx.guild_id, msgId)
            new = True

        duos = self.db.getCouples(msgId)
        for duo in duos:
            if emjName == duo[0] or roleId == duo[1]:
                await ctx.respond("The emoji or the role is already used in the message")

                if new:
                    self.db.delMsg(msgId)
                return

        try:
            await msg.add_reaction(emjName)
        except (NotFound, InvalidArgument):
            await ctx.respond("Unknown error with the emoji")
            if new:
                await self.db.delMsg(msgId)
            return

        self.db.addCouple((emjName, roleId), msgId)
        await ctx.respond("Done !")


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))