import discord
from discord.ext import commands

import asyncio
import os
import sys

from database.database import DatabaseHandler

class Admin(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()

    @commands.command(hidden = True)
    @commands.is_owner() # Check if the author if the owner of the bot
    async def stop(self, ctx):
        await ctx.send("Stop !")
        await self.bot.close()

    @commands.command(hidden = True)
    @commands.is_owner()
    async def restart(self, ctx : commands.Context):
        await ctx.send("Restart !")
        await self.bot.close()
        print("*******************\n" + 
              "----- Restart -----\n" + 
              "*******************\n"
        )
        os.execv(sys.executable, ['python3'] + sys.argv)
        

    async def createCouple(self, ctx : commands.Context, duos : list) -> tuple:
        msg = "For the first part, react to this message with the emoji you want to add in the reaction role !\nError : "
        error = "None"
        config = await ctx.send("Go !")

        def checkReact(reaction : discord.Reaction, user : discord.User):
            return ctx.author.id == user.id and config.id == reaction.message.id

        def checkRole(message : discord.Message):
            return message.author.id == ctx.author.id and config.channel.id == message.channel.id

        test = False
        count = 0
        while not test:
            if count >= 3: # The user can fails 3 times before the end of the command
                await config.delete()
                await ctx.send("Too many fails, retry please")
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

    @commands.command(description="Set the message you replied to as a reaction role message")
    async def createReactRole(self, ctx : commands.Context, msgId : int):
        msg = await ctx.fetch_message(msgId)
        if msg is None:
            await ctx.message.reply("Wrong ID given for the message")
            return

        res = self.db.getMsg(msgId)
        if res is None or len(res) == 0:
            self.db.addMsg(ctx.guild.id, msgId)

        duos = self.db.getCouples(msgId)
        couple = await self.createCouple(ctx, duos)
        if couple is None:
            return

        self.db.addCouple(couple, msgId)
        await ctx.message.delete()
        await msg.add_reaction(couple[0])


def setup(bot : commands.Bot):
    bot.add_cog(Admin(bot))