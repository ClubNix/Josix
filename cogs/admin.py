import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option

import asyncio

from database.database import DatabaseHandler

class Admin(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()

    async def createCouple(self, ctx : ApplicationContext, duos : list) -> tuple:
        chan = ctx.channel

        msg = "For the first part, react to this message with the emoji you want to add in the reaction role !\nError : "
        error = "None"
        config = await chan.send("Go !")

        def checkReact(reaction : discord.Reaction, user : discord.User):
            return ctx.author.id == user.id and config.id == reaction.message.id

        def checkRole(message : discord.Message):
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
                error = "You've been too long too answer, retry"
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

    @commands.slash_command(description="Set the message you replied to as a reaction role message")
    @option(
        input_type=int,
        name="message_id",
        description="ID of the message to which you want to add a reaction-role",
        required=True
    )
    async def create_react_role(self, ctx : ApplicationContext, msg_id : int):
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

        duos = self.db.getCouples(msg_id)
        couple = await self.createCouple(ctx, duos)
        if couple is None:
            return

        self.db.addCouple(couple, msg_id)
        await msg.add_reaction(couple[0])
        await ctx.respond("Done !")

    @commands.slash_command(description="Clear messages from the channel")
    @commands.has_permissions(manage_messages=True)
    @option(
        input_type=int,
        name="limit",
        description="Limit of messages to delete (default 10)",
        default=10
    )
    async def clear(self, ctx: ApplicationContext, limit : int):
        await ctx.channel.purge(limit=limit)
        await ctx.respond("Done !")


def setup(bot : commands.Bot):
    bot.add_cog(Admin(bot))