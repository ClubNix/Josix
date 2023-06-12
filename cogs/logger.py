import discord
from discord.ext import commands
from discord.ui.select import Select
from discord import AutoModRule, AutoModActionExecutionEvent
from discord import Guild, TextChannel, Emoji, GuildSticker, Role, PermissionOverwrite
from discord import User, Member, RawMemberRemoveEvent, Embed
from discord.abc import GuildChannel

import os
import logwrite as log

from database.database import DatabaseHandler
from enum import IntEnum
from typing import Sequence
from datetime import datetime as dt


class Logs(IntEnum):
    """Enumerator that represents all differents logs"""
    AUTOMOD = 1
    GUILD_UPDATE = 2
    CHANNEL_LIFE = 3
    CHANNEL_UPDATE = 4
    ROLE_LIFE = 5
    ROLE_UPDATE = 6
    EMOJIS_UPDATE = 7
    STICKERS_UPDATE = 8
    WEBHOOKS_UPDATE = 9
    BANS = 10
    MEMBER_JOIN = 11
    MEMBER_UPDATE = 12
    USER_UPDATE = 13


class LoggerView(discord.ui.View):
    """
    Represents the view for the set_logger command

    Attributes
    ----------
    db : DatabaseHandler
        Handler for the database
    keep : bool
        Value representing if the old selected logs should be keep or not

    Methods
    -------
    select_callback(select: Select, interaction: Interaction):
        A callback called when the view is executed
    """
    def __init__(self, db: DatabaseHandler, keep: bool) -> None:
        super().__init__(disable_on_timeout=True, timeout=180.0)
        self.db = db
        self.keep = keep

    @discord.ui.select(
        placeholder="Choose the desired logs",
        min_values=0,
        max_values=12,
        options=[
            discord.SelectOption(
                label="Automod events", value=str(Logs.AUTOMOD.value),
                description="All events related to the discord automod"
            ),
            discord.SelectOption(
                label="Server updates", value=str(Logs.GUILD_UPDATE.value),
                description="All the updates of the server"
            ),
            discord.SelectOption(
                label="Channel created or deleted", value=str(Logs.CHANNEL_LIFE.value),
                description="Creation or deletion of a channel"
            ),
            discord.SelectOption(
                label="Channel updates", value=str(Logs.CHANNEL_UPDATE.value),
                description="All updates of a channel"
            ),
            discord.SelectOption(
                label="Role created or deleted", value=str(Logs.ROLE_LIFE.value),
                description="Creation or deletion of a role"
            ),
            discord.SelectOption(
                label="Role updates", value=str(Logs.ROLE_UPDATE.value),
                description="All updates of a role"
            ),
            discord.SelectOption(
                label="Emoji updates", value=str(Logs.EMOJIS_UPDATE.value),
                description="All updates on the emojis"
            ),
            discord.SelectOption(
                label="Stickers updates", value=str(Logs.STICKERS_UPDATE.value),
                description="All updates on the stickers"
            ),
            discord.SelectOption(
                label="Webhooks updates", value=str(Logs.WEBHOOKS_UPDATE.value),
                description="All updates on the webhooks"
            ),
            discord.SelectOption(
                label="Bans", value=str(Logs.BANS.value),
                description="Bans and unbans of members"
            ),
            discord.SelectOption(
                label="Joins", value=str(Logs.MEMBER_JOIN.value),
                description="A member joins or leaves the server"
            ),
            discord.SelectOption(
                label="Member update", value=str(Logs.MEMBER_UPDATE.value),
                description="All updates of user's server profile"
            ),
            discord.SelectOption(
                label="User update", value=str(Logs.USER_UPDATE.value),
                description="All updates on users"
            ),
        ]
    )
    async def select_callback(self, select: Select, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            await interaction.response.edit_message(content="Impossible to reach the server")
            return

        idGuild = interaction.guild_id
        if not self.db.getGuild(idGuild):
            self.db.addGuild(idGuild)
        
        try:
            old = self.db.getSelectLogs(idGuild)
        except Exception as e:
            log.writeError(log.formatError(e))
            old = None

        oldLogs = []
        if old and old.logs:
            oldLogs = old.logs

        try:
            values = list(map(int, select.values))
        except ValueError as e:
            log.writeError(log.formatError(e))
            await interaction.response.edit_message(content="Unknown error occured")
            return

        for logValue in oldLogs:
            if logValue not in values and self.keep:
                values.append(logValue)

        try:
            self.db.updateLogSelects(idGuild, values)
        except Exception as e:
            log.writeError(log.formatError(e))
            await interaction.response.edit_message(content="Unknown error occured")
            return

        await interaction.response.edit_message(content="Your logs selection has been updated")
        self.disable_all_items()
        self.stop()


class Logger(commands.Cog):
    """
    Represents the logs handler extension of the bot

    Attributes
    ----------
    bot : discord.ext.commands.Bot
        The bot that loaded this extension
    db : DatabaseHandler
        A handler to perform requests on the database
    addColor : int
        Hexadecimal green color for embeds
    updColor : int
        Hexadecimal yellow color for embeds
    noColor : int
        Hexadecimal red color for embeds 
    """

    addColor = 0x1cb82b
    updColor = 0xf1c232
    noColor = 0xc90e3a

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))
        self._updateLogs()

    def _updateLogs(self):
        logs = [(i.lower(), v.value) for i, v in Logs._member_map_.items()]
        self.db.updateLogsEntries(logs)

    async def checkLogStatus(self, idGuild: int, idLog: int) -> discord.TextChannel | None:
        """
        Check if the guild has enabled this log

        Retrieves the logs of the guild and check if this log is obtained.
        Then returns the channel where the logs are displayed

        Parameters
        ----------
        idGuild : int
            ID of the guild where the log is called
        idLog : int
            ID of the called log

        Returns
        -------
        TextChannel | None
            The text channel that displays the logs
        """
        guildLogs = self.db.getSelectLogs(idGuild)
        dbGuild = self.db.getGuild(idGuild)
        
        if not (guildLogs or dbGuild) or idLog not in guildLogs.logs:
            return None
        return self.bot.get_channel(dbGuild.logNews)

#
# Automod logs
#

    async def automod_create_update(self, rule: AutoModRule, create: bool) -> None:
        chan: discord.TextChannel = await self.checkLogStatus(rule.guild_id, Logs.AUTOMOD)
        if not chan:
            return

        creator = rule.creator
        embed = Embed(
            title="Automod rule " + ("created" if create else "updated"),
            description=rule.name,
            color=Logger.addColor if create else Logger.updColor
        )
        if creator: embed.set_author(name=creator, icon_url=creator.display_avatar)
        embed.add_field(name="Trigger", value=rule.trigger_type.name)
        embed.add_field(name="Enabled", value=rule.enabled, inline=False)
        embed.add_field(name="Actions", value=", ".join([i.type.name for i in rule.actions]))
        embed.set_footer(text=f"ID : {rule.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_auto_moderation_rule_create(self, rule: AutoModRule):
        await self.automod_create_update(rule, True)

    @commands.Cog.listener()
    async def on_auto_moderation_rule_delete(self, rule: AutoModRule):
        chan: TextChannel = await self.checkLogStatus(rule.guild_id, Logs.AUTOMOD)
        if not chan:
            return

        creator = rule.creator
        embed = Embed(
            title="Automod rule deleted",
            description=rule.name,
            color=Logger.noColor
        )
        if creator: embed.set_author(name=creator, icon_url=creator.display_avatar)
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_auto_moderation_rule_update(self, rule: AutoModRule):
        await self.automod_create_update(rule, False)

    @commands.Cog.listener()
    async def on_auto_moderation_action_execution(self, payload: AutoModActionExecutionEvent):
        chan: TextChannel = await self.checkLogStatus(payload.guild_id)
        if not chan:
            return
        
        rule = await payload.guild.fetch_auto_moderation_rule(payload.rule_id)
        embed = Embed(
            title="Automod rule executed",
            description=rule.name,
            color=Logger.noColor
        )
        embed.set_author(name=payload.member, icon_url=payload.member.display_avatar)
        embed.set_thumbnail(url=payload.member.display_avatar)
        embed.add_field(name="Action", value=payload.action.type.name)
        embed.add_field(name="Key-word", value=payload.matched_keyword)
        embed.add_field(name="Trigger", value=payload.matched_content)
        embed.add_field(name="Content", value=payload.content[:1024], inline=False)
        embed.set_footer(text=f"ID : {rule.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        await chan.send(embed=embed)

#
# Channel logs
#

    async def _channel_embed(self, channel: GuildChannel, title: str, color: int) -> Embed:
        embed = Embed(
            title=title,
            color=color
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(name="Name", value=channel.name)
        embed.add_field(name="Category", value=channel.category)
        embed.add_field(
            name="Overwrites",
            value=", ".join([target.mention for target in channel.overwrites.keys()])[:1023],
            inline=False
        )
        embed.set_footer(text=f"ID : {channel.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        return embed

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: GuildChannel):
        chan: TextChannel = await self.checkLogStatus(channel.guild.id, Logs.CHANNEL_LIFE)
        if not chan:
            return
        embed = await self._channel_embed(channel, "Channel created", Logger.addColor)
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        chan: TextChannel = await self.checkLogStatus(channel.guild.id, Logs.CHANNEL_LIFE)
        if not chan:
            return
        embed = await self._channel_embed(channel, "Channel deleted", Logger.noColor)
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: GuildChannel, after: GuildChannel):
        chan: TextChannel = await self.checkLogStatus(before.guild.id, Logs.CHANNEL_UPDATE)
        if not chan:
            return

        embed = Embed(
            title="Channel updated",
            color=Logger.updColor
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.set_footer(text=f"ID : {before.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

        if before.name != after.name:
            embed.title = "Channel name updated"
            embed.description = f"{before.name} **-->** {after.name}"
        elif before.category != after.category:
            embed.title = "Channel category updated"
            embed.description = f"{before.category} **-->** {after.category}"
            embed.add_field(name="Name", value=after.name)
        else:
            embed.add_field(name="Name", value=after.name)
            test = False
            updTarget: Member | Role = None
            updPerms : PermissionOverwrite = None

            if len(before.overwrites) < len(after.overwrites):
                test = True
                for key in after.overwrites:
                    if key not in before.overwrites.keys():
                        continue

                    updTarget = key
                    updPerms = after.overwrites[key]
                    break

            elif len(before.overwrites) > len(after.overwrites):
                test = True
                for key in before.overwrites:
                    if key in after.overwrites.keys():
                        continue

                    updTarget = key
                    break
            else:
                for key in after.overwrites:
                    if before.overwrites[key] != after.overwrites[key]:
                        test = True
                        updTarget = key
                        updPerms = after.overwrites[key]

            if not (test or updTarget):
                return

            embed.title = f"Permissions changed for {updTarget.name} in {after.name}"
            allows = []
            disallows = []
            for perm in iter(updPerms):
                allows.append(perm[0]) if perm[1] else disallows.append(perm[0])

            if updPerms:
                embed.add_field(
                    name="Allowed permissions ✅",
                    value=", ".join(allows)[:1023],
                    inline=False
                )
                embed.add_field(
                    name="Disallowed permissions ❌",
                    value=", ".join(disallows)[:1023],
                    inline=False
                )
            else:
                embed.description = "Permissions deleted"
        await chan.send(embed=embed)

#
# Role logs
#

    async def _role_embed(self, role: Role, title: str, color: int) -> Embed:
        embed = Embed(
            title=title,
            color=color
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="Color", value=role.color)
        embed.add_field(
            name="Permissions",
            value=", ".join([perm for perm, allow in role.permissions if allow])[:1023],
            inline=False
        )
        embed.set_footer(text=f"ID : {role.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        return embed

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: Role):
        chan: TextChannel = await self.checkLogStatus(role.guild.id, Logs.ROLE_LIFE)
        if not chan:
            return
        embed = await self._role_embed(role, "Role created", Logger.addColor)
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: Role):
        chan: TextChannel = await self.checkLogStatus(role.guild.id, Logs.ROLE_LIFE)
        if not chan:
            return
        embed = await self._role_embed(role, "Role deleted", Logger.noColor)
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: Role, after: Role):
        chan: TextChannel = await self.checkLogStatus(before.guild.id, Logs.ROLE_UPDATE)
        if not chan:
            return

        embed = Embed(
            title=f"Role {before.name} updated",
            color=Logger.updColor
        )
        embed.set_footer(text=f"ID : {after.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

        if before.name != after.name:
            embed.add_field(name="Name", value=f"{before.name} **-->** {after.name}", inline=False)
        if before.color != after.color:
            embed.add_field(name="Color", value=f"{before.color} **-->** {after.color}", inline=False)
        if before.mentionable != after.mentionable:
            embed.add_field(name="Mentionable", value=after.mentionable, inline=False)
        if before.hoist != after.hoist:
            embed.add_field(name="Separated", value=after.hoist, inline=False)

        if before.permissions != after.permissions:
            embed.add_field(
                name="Permissions",
                value=", ".join([perm for perm, allow in after.permissions if allow])[:1023],
                inline=False
            )
        if len(embed.fields) > 0:
            await chan.send(embed=embed)

#
# Update logs
#

    def _emoji_embed(self, emoji: Emoji, create: bool) -> Embed:
        embed = Embed(
            title=("New emoji" if create else "Emoji deleted"),
            color=(Logger.addColor if create else Logger.noColor)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(name="Emoji", value=emoji)
        embed.add_field(name="Name", value=emoji.name)
        embed.add_field(name= '\u200B', value= '\u200B')
        if emoji.user: embed.add_field(name="Creator", value=emoji.user.mention)
        embed.add_field(name="Animated", value=emoji.animated)
        embed.set_footer(text=f"ID : {emoji.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        return embed

    def _sticker_embed(self, sticker: GuildSticker, create: bool) -> Embed:
        embed = Embed(
            title=("New sticker" if create else "Sticker deleted"),
            description=sticker.description,
            color=(Logger.addColor if create else Logger.noColor)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        if sticker.url: embed.set_image(url=sticker.url)
        embed.add_field(name="Name", value=sticker.name)
        if sticker.user: embed.add_field(name="Creator", value=sticker.user.mention)
        embed.add_field(name="Format", value=sticker.format.name)
        embed.set_footer(text=f"ID : {sticker.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        return embed


    @commands.Cog.listener()
    async def on_guild_update(self, before: Guild, after: Guild):
        chan: TextChannel = await self.checkLogStatus(before.id, Logs.GUILD_UPDATE)
        if not chan:
            return

        embed = Embed(
            title="Server updated",
            color=Logger.updColor
        )
        embed.set_footer(text=f"ID : {after.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        if after.icon: embed.set_thumbnail(url=after.icon)

        if before.afk_channel != after.afk_channel:
            bf = before.afk_channel.mention if before.afk_channel else "None"
            af = after.afk_channel.mention if after.afk_channel else "None"
            embed.add_field(name="AFK Channel", value=f"{bf} **-->** {af}", inline=False)
        if before.afk_timeout != after.afk_timeout:
            embed.add_field(name="AFK Timeout", value=f"{before.afk_timeout} **-->** {after.afk_timeout}", inline=False)
        if before.banner != after.banner:
            embed.add_field(name="Banner", value=f"[before]({before.banner}) **-->** [after]({after.banner})", inline=False)
        if before.description != after.description:
            embed.add_field(name="Description", value=f"{before.description} **-->** {after}"[:1023], inline=False)
        if before.explicit_content_filter != after.explicit_content_filter:
            embed.add_field(name="Filter", value=f"{before.explicit_content_filter} **-->** {after.explicit_content_filter}", inline=False)
        if before.icon != after.icon:
            embed.add_field(name="Icon", value=f"[before]({before.icon}) **-->** [after]({after.icon})", inline=False)
        if before.mfa_level != after.mfa_level:
            embed.add_field(name="Staff secure level", value=f"{before.mfa_level} **-->** {after.mfa_level}", inline=False)
        if before.name != after.name:
            embed.add_field(name="Name", value=f"{before.name} **-->** {after.name}", inline=False)
        if before.nsfw_level != after.nsfw_level:
            embed.add_field(name="NSFW Level", value=f"{before.nsfw_level} **-->** {after.nsfw_level}", inline=False)
        if before.verification_level != after.verification_level:
            embed.add_field(name="Verification level", value=f"{before.verification_level} **-->** {after.verification_level}", inline=False)

        if len(embed.fields) > 0:
            await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: Guild, before: Sequence[Emoji], after: Sequence[Emoji]):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.EMOJIS_UPDATE)
        if not chan:
            return

        if len(before) < len(after):
            res: Emoji = None
            for emoji in after:
                if emoji not in before:
                    res = emoji
                    break

            if not res:
                return
            await chan.send(embed=self._emoji_embed(res, True))

        elif len(before) > len(after):
            res: Emoji = None
            for emoji in before:
                if emoji not in after:
                    res = emoji
                    break

            if not res:
                return
            await chan.send(embed=self._emoji_embed(res, False))

        else:
            resB: Emoji = None
            resA: Emoji = None
            for i, emojiB in enumerate(before):
                emojiA = after[i]
                if emojiB.name != emojiA.name:
                    resB, resA = emojiB, emojiA

            if not (resB or resA):
                return

            embed = Embed(title=f"Emoji {resA.name} updated", color=Logger.updColor)
            embed.set_thumbnail(url=self.bot.user.display_avatar)
            embed.set_footer(text=f"ID : {resA.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

            if resB.animated != resA.animated:
                embed.add_field(name="Animated", value=f"{resB.animated} **-->** {resA.animated}", inline=False)
            if resB.available != resA.available:
                embed.add_field(name="Available", value=f"{resB.available} **-->** {resA.available}", inline=False)
            if resB.name != resA.name:
                embed.add_field(name="Name", value=f"{resB.name} **-->** {resA.name}", inline=False)
            if resB.roles != resA.roles:
                embed.add_field(name="Roles allowed before", value=", ".join(map(str, resB.roles)), inline=False)
                embed.add_field(name="Roles allowed after", value=", ".join(map(str, resA.roles)), inline=False)
            if len(embed.fields) > 0:
                await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild: Guild, before: Sequence[GuildSticker], after: Sequence[GuildSticker]):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.STICKERS_UPDATE)
        if not chan:
            return

        if len(before) < len(after):
            res: GuildSticker = None
            for sticker in after:
                if sticker not in before:
                    res = sticker
                    break

            if not res:
                return
            await chan.send(embed=self._sticker_embed(res, True))

        elif len(before) > len(after):
            res: Emoji = None
            for sticker in before:
                if sticker not in after:
                    res = sticker
                    break

            if not res:
                return
            await chan.send(embed=self._sticker_embed(res, False))

        else:
            resB: GuildSticker = None
            resA: GuildSticker = None
            for i, stickerB in enumerate(before):
                stickerA = after[i]
                if stickerB.name != stickerA.name or stickerB.emoji != stickerA.emoji:
                    resB, resA = stickerB, stickerA

            if not (resB or resA):
                return

            embed = Embed(title=f"Sticker {resA.name} updated", color=Logger.updColor)
            embed.set_thumbnail(url=self.bot.user.display_avatar)
            embed.set_footer(text=f"ID : {resA.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

            if resB.available != resA.available:
                embed.add_field(name="Available", value=f"{resB.available} **-->** {resA.available}", inline=False)
            if resB.description != resA.description:
                embed.add_field(name="Description", value=f"{resB.description} **-->** {resA.description}"[:1023], inline=False)
            if resB.emoji != resA.emoji:
                embed.add_field(name="Emoji", value=f"{resB.emoji} **-->** {resA.emoji}", inline=False)
            if resB.format != resA.format:
                embed.add_field(name="Format", value=f"{resB.format.name} **-->** {resA.format.name}", inline=False)
            if resB.name != resA.name:
                embed.add_field(name="Name", value=f"{resB.name} **-->** {resA.name}", inline=False)
            if len(embed.fields) > 0:
                await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: GuildChannel):
        chan: TextChannel = await self.checkLogStatus(channel.guild.id, Logs.WEBHOOKS_UPDATE)
        if not chan:
            return

        embed = Embed(title="Webhook update", color=Logger.updColor)
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(name="Name", value=channel.name)
        embed.add_field(name="Category", value=channel.category)
        embed.set_footer(text=f"{channel.mention} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        await chan.send(embed=embed)

#
# Member logs
#

    def _join_embed(self, user: discord.User | Member, join: bool) -> Embed:
        title = (
            f"{user.name} joined the server" if join else f"{user.name} left the server"
        )
        color = Logger.addColor if join else Logger.noColor
        embed = discord.Embed(title=title, color=color)
        embed.set_thumbnail(url=user.display_avatar)
        embed.add_field(name="Name", value=user.name)
        embed.add_field(name="Creation date", value=dt.strftime(user.created_at, '%d/%m/%Y'))
        embed.set_footer(text=f"{user.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")
        return embed

    @commands.Cog.listener()
    async def on_member_ban(self, guild: Guild, user: User | Member):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.BANS)
        if not chan:
            return

        embed = discord.Embed(title=f"User {user.name} banned", color=Logger.noColor)
        embed.set_thumbnail(url=user.display_avatar)
        embed.add_field(name="Name", value=user.name)
        embed.set_footer(text=f"{user.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

        async for ban in guild.bans():
            if ban.user == user:
                if ban.reason:
                    embed.add_field(name="Reason", value=ban.reason[:1023], inline=False)
                break
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: Guild, user: User):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.BANS)
        if not chan:
            return

        embed = discord.Embed(title=f"User {user.name} unbanned", color=Logger.updColor)
        embed.set_thumbnail(url=user.display_avatar)
        embed.add_field(name="Name", value=user.name)
        embed.set_footer(text=f"{user.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

        async for unban in guild.audit_logs(oldest_first=True, action=discord.AuditLogAction.unban):
            if unban.user:
                if unban.reason:
                    embed.add_field(name="Reason", value=unban.reason[:1023])
                break
        await chan.send(embed=embed) 

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        chan: TextChannel = await self.checkLogStatus(member.guild.id, Logs.MEMBER_JOIN)
        if not chan:
            return

        embed = self._join_embed(member, True)
        embed.description = member.mention
        await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: RawMemberRemoveEvent):
        chan: TextChannel = await self.checkLogStatus(payload.guild_id, Logs.MEMBER_JOIN)
        if not chan:
            return

        await chan.send(embed=self._join_embed(payload.user, False))

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        chan: TextChannel = await self.checkLogStatus(before.guild.id, Logs.MEMBER_UPDATE)
        if not chan:
            return

        embed = Embed(
            title="",
            description=f"{after.mention} updated their profile",
            color=Logger.updColor
        )
        embed.set_thumbnail(url=after.display_avatar)
        embed.set_author(name=after, icon_url=after.display_avatar)
        embed.set_footer(text=f"{after.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

        if before.nick != after.nick:
            embed.add_field(name="Nickname", value=f"{before.nick} **-->** {after.nick}", inline=False)
        if before.timed_out != after.timed_out:
            embed.add_field(name="Timeout", value=f"{before.timed_out} **-->** {after.timed_out}", inline=False)
            if after.timed_out and after.communication_disabled_until:
                embed.add_field(
                    name="End",
                    value=dt.strftime(after.communication_disabled_until, '%d/%m/%Y %H:%M:%S'),
                    inline=False
                )
        if len(embed.fields) > 0:
            await chan.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before: User, after: User):
        for guild in after.mutual_guilds:
            chan: TextChannel = await self.checkLogStatus(guild.id, Logs.USER_UPDATE)
            if not chan:
                return

            embed = Embed(
                title="",
                description=f"{after.mention} updated their profile",
                color=Logger.updColor
            )
            embed.set_thumbnail(url=after.display_avatar)
            embed.set_author(name=after, icon_url=after.display_avatar)
            embed.set_footer(text=f"{after.id} • {dt.strftime(dt.now(), '%d/%m/%Y %H:%M')}")

            if before.avatar != after.avatar:
                embed.add_field(name="Avatar", value=f"[before]({before.avatar}) **-->** [after]({after.avatar})", inline=False)
            if before.name != after.name:
                embed.add_field(name="Username", value=f"{before.name} **-->** {after.name}", inline=False)
            
            if len(embed.fields) > 0:
                await chan.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Logger(bot))
