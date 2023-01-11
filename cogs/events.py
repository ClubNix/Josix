import discord
from discord.ext import commands
from discord import RawReactionActionEvent, ApplicationCommandError, ApplicationCommandInvokeError

from database.database import DatabaseHandler
from typing import Union

import logwrite as log

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()

    async def updateRole(self, payload: RawReactionActionEvent, add: bool):
        emoji = payload.emoji
        if emoji.is_custom_emoji():
            return

        msgId = payload.message_id
        resMsg = self.db.getMsg(msgId)
        if resMsg is None or len(resMsg) == 0:
            return

        if payload.message_id in resMsg:
            userId = payload.user_id
            guildId = payload.guild_id
            emojiName = emoji.name

            guild = self.bot.get_guild(guildId)
            member = guild.get_member(userId)

            resRoles = self.db.getRoleFromReact(msgId, emojiName)
            if resRoles is None:
                return

            roleId = resRoles[0]
            role = guild.get_role(roleId)

            if add:
                if not member.get_role(roleId):
                    await member.add_roles(role)
            else:
                if member.get_role(roleId):
                    await member.remove_roles(role)


##### ================================================== #####
##### ================================================== #####
##### ================================================== #####

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        await self.updateRole(payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        await self.updateRole(payload, False)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if not isinstance(thread.parent, discord.ForumChannel):
            return
        await thread.send("This thread is now open. You can close it automatically by using `/close`")

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Union[ApplicationCommandError, ApplicationCommandInvokeError]):
        await ctx.respond("An error occured")
        log.writeError(str(error))
        

def setup(bot: commands.Bot):
    bot.add_cog(Events(bot))