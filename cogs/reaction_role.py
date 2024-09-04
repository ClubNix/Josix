import discord
from discord import (
    RawBulkMessageDeleteEvent,
    RawMessageDeleteEvent,
    RawReactionActionEvent,
)
from discord.ext import commands

import pkg.logwrite as log
from database.services import reactrole_service
from josix import Josix
from pkg.bot_utils import JosixCog


class ReactionRole(JosixCog):
    """
    Represents the Reaction Role extension of the bot

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    """

    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot

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
        handler = self.bot.get_handler()
        emoji = payload.emoji
        if emoji.is_custom_emoji():
            return

        msgId = payload.message_id
        resMsg = reactrole_service.get_reaction_message(handler, msgId)
        if not resMsg:
            return

        if payload.message_id == resMsg.id:
            userId = payload.user_id
            guildId = payload.guild_id
            emojiName = emoji.name

            if not guildId:
                return

            if not (guild := self.bot.get_guild(guildId)) and not (guild := await self.bot.fetch_guild(guildId)):
                return

            if not (member := guild.get_member(userId)) and not (member := await guild.fetch_member(userId)):
                return

            if member.bot:
                return

            resRole = reactrole_service.get_role_from_reaction(handler, msgId, emojiName)
            if resRole is None:
                return

            roleId = resRole
            if not (role := guild.get_role(roleId)):
                for val in await guild.fetch_roles():
                    if val.id == roleId:
                        role = val
                        break
                else:
                    return

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
            log.writeError(log.formatError(e))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        try:
            await self.updateRole(payload, False)
        except Exception as e:
            log.writeError(log.formatError(e))
        
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        handler = self.bot.get_handler()
        try:
            if not reactrole_service.get_reaction_message(handler, payload.message_id):
                return

            reactrole_service.delete_message_react(handler, payload.message_id)
        except Exception as e:
            log.writeError(log.formatError(e))

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: RawBulkMessageDeleteEvent):
        handler = self.bot.get_handler()
        try:
            for msg_id in payload.message_ids:
                if not reactrole_service.get_reaction_message(handler, msg_id):
                    continue

                reactrole_service.delete_message_react(handler, msg_id)
        except Exception as e:
            log.writeError(log.formatError(e))

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        handler = self.bot.get_handler()
        try:
            couples = reactrole_service.get_couple_from_role(handler, role.id)
            if not couples:
                return

            for couple in couples:
                reactrole_service.delete_reaction_couple(handler, couple.id)
        except Exception as e:
            log.writeError(log.formatError(e))

def setup(bot: Josix):
    bot.add_cog(ReactionRole(bot, False))
