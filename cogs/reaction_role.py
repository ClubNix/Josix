import discord
from discord.ext import commands
from discord import RawReactionActionEvent, RawMessageDeleteEvent, RawBulkMessageDeleteEvent

import os
import logwrite as log

from database.database import DatabaseHandler
from bot_utils import JosixCog


class ReactionRole(JosixCog):
    """
    Represents the Reaction Role extension of the bot

    Attributes
    ----------
    bot : discord.ext.commands.Bot
        The bot that loaded this extension
    db : DatabaseHandler
        The database handler of this extension
    """

    def __init__(self, bot: commands.Bot, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

    async def updateRole(self, payload: RawReactionActionEvent, add: bool) -> None:
        """
        Update the role of a user when it interacts with a reaction role message

        Check if the message is a reaction role message and if the reaction is not a
        custom emoji.
        Then retrieves the role associated with the reaction and add or remove it from the user

        Parameters
        ----------
        payload : RawReactionActionEvent
            The action event launched by the player
        add : bool
            Boolean that indicates if the user added or removed a reaction
        """
        emoji = payload.emoji
        if emoji.is_custom_emoji():
            return

        msgId = payload.message_id
        resMsg = self.db.getMsg(msgId)
        if not resMsg:
            return

        if payload.message_id == resMsg.id:
            userId = payload.user_id
            guildId = payload.guild_id
            emojiName = emoji.name

            guild = self.bot.get_guild(guildId)
            member = guild.get_member(userId)

            resRole = self.db.getRoleFromReact(msgId, emojiName)
            if resRole is None:
                return

            roleId = resRole
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
                self.db.delReactCouple(couple.id)
        except Exception as e:
            log.writeLog(log.formatError(e))

def setup(bot: commands.Bot):
    bot.add_cog(ReactionRole(bot, False))
