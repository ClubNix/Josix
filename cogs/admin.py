import discord
from discord.ext import commands

import asyncio
from database.database import DatabaseHandler

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseHandler()

    async def getCouple(self, ctx, duos) -> tuple:
        msg = "For the first part, react to this message with the emoji you want to add in the reaction role !\n error :"
        error = "None"
        config = await ctx.send("Go !")

        def checkReact(reaction, user):
            return ctx.author.id == user.id and config.id == reaction.message.id

        def checkRole(message):
            return message.author.id == config.author.id and config.channel.id == message.channel.id

        test = True
        count = 0
        while test:
            if count >= 3: # The user can fails 3 times before the end of the command
                config.delete()
                await ctx.send("Too many fails, retry please")
                return (None, None)

            test = True

            # Displaying the configuration messages
            config.edit(msg + error)
            config.clear_reactions()

            try:    
                reaction = await self.bot.wait_for('reaction_add', check=checkReact, timeout=60)[0]

                if reaction.is_custom_emoji():
                    reaction = reaction.emoji
                    if reaction not in ctx.guild.emojis:
                        test = False
                        error = "This emoji is not available in this server"
                        continue
                
                for duo in duos:
                    if reaction in duo:
                        test = False
                        error = "This emoji is already linked to a role in this reaction role message"
                        continue

            except asyncio.TimeoutError as _:
                test = False
                error = "You've been too long too answer"
                continue

            try:    
                response = await self.bot.wait_for('message', check=checkRole, timeout=60)
                mentions = response.role_mentions
                response.delete()

                if len(mentions) > 0:
                    role = mentions[0]
                else:
                    try:
                        role = self.bot.get_role(int(response))
                        if role is None:
                            test = False
                            error = "This role is already linked to an emoji in this reaction role message"
                            continue

                    except ValueError as _:
                        test = False
                        error = "Wrong role ID given"

                if role not in ctx.guild.roles:
                    test = False
                    error = "This role not available in this server"
                    continue
                
            except asyncio.TimeoutError as _:
                test = False
                error = "You've been too long too answer"
                continue

        config.delete()
        return (reaction, role)

    @commands.command(description="Set the message you replied to as a reaction role message")
    async def createReactRole(self, ctx, msgID : int):
        msg = self.bot.get_message(msgID)
        if msg is None:
            self.ctx.message.reply("Wrong ID given for the message")
            return

        duos = []

        self.getCouple(ctx, duos)


def setup(bot):
    bot.add_cog(Admin(bot))