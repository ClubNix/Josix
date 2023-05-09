import discord
from discord.ext import commands
from discord import RawReactionActionEvent, RawMessageDeleteEvent, RawBulkMessageDeleteEvent

from database.database import DatabaseHandler

import os
import logwrite as log


class ReactionRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        try:
            await self.updateRole(payload, True)
        except Exception as e:
            log.writeLog(log.formatError(e))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        try:
            await self.updateRole(payload, False)
        except Exception as e:
            log.writeLog(log.formatError(e))
        
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        try:
            if not self.db.getMsg(payload.message_id):
                return

            self.db.delMessageReact(payload.message_id)
        except Exception as e:
            log.writeLog(log.formatError(e))

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: RawBulkMessageDeleteEvent):
        try:
            for msg_id in payload.message_ids:
                if not self.db.getMsg(msg_id):
                    continue

                self.db.delMessageReact(msg_id)
        except Exception as e:
            log.writeLog(log.formatError(e))

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        try:
            couples = self.db.getCoupleFromRole(role.id)
            if not couples:
                return

            for couple in couples:
                self.db.delReactCouple(couple[0])
        except Exception as e:
            log.writeLog(log.formatError(e))

def setup(bot: commands.Bot):
    bot.add_cog(ReactionRole(bot))
