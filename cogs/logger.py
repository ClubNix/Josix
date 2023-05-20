import discord
from discord.ext import commands
from discord.ui.select import Select
from discord import AutoModRule, AutoModActionExecutionEvent
from discord import Guild, TextChannel, Emoji, GuildSticker, Role, PermissionOverwrite
from discord import User, Member, RawMemberRemoveEvent
from discord.abc import GuildChannel

from database.database import DatabaseHandler
from enum import IntEnum
from typing import Sequence
from time import time, mktime
from datetime import datetime as dt

import os
import logwrite as log


class Logs(IntEnum):
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
    def __init__(self, db: DatabaseHandler) -> None:
        super().__init__(disable_on_timeout=True, timeout=180.0)
        self.db = db

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
                label="User update", value=str(Logs.MEMBER_UPDATE.value),
                description="All updates on the member of the server"
            ),
            discord.SelectOption(
                label="User update", value=str(Logs.USER_UPDATE.value),
                description="All updates on users"
            ),
        ]
    )
    async def select_callback(self, select: Select, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            return

        try:
            values = list(map(int, select.values))
        except ValueError as e:
            log.writeError(log.formatError(e))
            return

        self.db.updateLogSelects(interaction.guild_id, values)
        await interaction.response.edit_message(content="Your logs selection has been updated")
        self.disable_all_items()
        self.stop()


class Logger(commands.Cog):
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
        embed = discord.Embed(
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
        embed = discord.Embed(
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
        embed = discord.Embed(
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

    async def _channel_embed(self, channel: GuildChannel, title: str, color: int) -> discord.Embed:
        embed = discord.Embed(
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

        embed = discord.Embed(
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

    async def _role_embed(self, role: Role, title: str, color: int) -> discord.Embed:
        embed = discord.Embed(
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

        embed = discord.Embed(
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
        await chan.send(embed=embed)

#
# Update logs
#

    @commands.Cog.listener()
    async def on_guild_update(self, before: Guild, after: Guild):
        chan: TextChannel = await self.checkLogStatus(before.id, Logs.GUILD_UPDATE)
        if not chan:
            return

        embed = discord.Embed(
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
            embed.add_field(name="Banner", value=f"[before]{before.banner} **-->** [after]{after.banner}", inline=False)
        if before.description != after.description:
            embed.add_field(name="Description", value=f"{before.description} **-->** {after}"[:1023], inline=False)
        if before.explicit_content_filter != after.explicit_content_filter:
            embed.add_field(name="Filter", value=f"{before.explicit_content_filter} **-->** {after.explicit_content_filter}", inline=False)
        if before.icon != after.icon:
            embed.add_field(name="Banner", value=f"[before]{before.icon} **-->** [after]{after.icon}", inline=False)
        if before.mfa_level != after.mfa_level:
            embed.add_field(name="Staff secure level", value=f"{before.mfa_level} **-->** {after.mfa_level}", inline=False)
        if before.name != after.name:
            embed.add_field(name="Name", value=f"{before.name} **-->** {after.name}", inline=False)
        if before.nsfw_level != after.nsfw_level:
            embed.add_field(name="NSFW Level", value=f"{before.nsfw_level} **-->** {after.nsfw_level}", inline=False)
        if before.verification_level != after.verification_level:
            embed.add_field(name="Verification level", value=f"{before.verification_level} **-->** {after.verification_level}", inline=False)
        await chan.send(embed=embed)
        

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: Guild, before: Sequence[Emoji], after: Sequence[Emoji]):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.EMOJIS_UPDATE)
        if not chan:
            return

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild: Guild, before: Sequence[GuildSticker], after: Sequence[GuildSticker]):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.STICKERS_UPDATE)
        if not chan:
            return

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: GuildChannel):
        chan: TextChannel = await self.checkLogStatus(channel.guild.id, Logs.WEBHOOKS_UPDATE)
        if not chan:
            return

        embed = discord.Embed(title="Webhook update", color=Logger.updColor)
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.add_field(name="Name", value=channel.name)
        embed.add_field(name="Category", value=channel.category)
        embed.set_footer(text=f"{channel.mention} • <t:{int(time())}:f>")
        await chan.send(embed=embed)

#
# Member logs
#

    @commands.Cog.listener()
    async def on_member_ban(self, guild: Guild, user: User | Member):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.BANS)
        if not chan:
            return

    @commands.Cog.listener()
    async def on_member_ban(self, guild: Guild, user: User):
        chan: TextChannel = await self.checkLogStatus(guild.id, Logs.BANS)
        if not chan:
            return

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        chan: TextChannel = await self.checkLogStatus(member.guild.id, Logs.MEMBER_JOIN)
        if not chan:
            return

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: RawMemberRemoveEvent):
        chan: TextChannel = await self.checkLogStatus(payload.guild_id, Logs.MEMBER_JOIN)
        if not chan:
            return

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        chan: TextChannel = await self.checkLogStatus(before.guild.id, Logs.MEMBER_UPDATE)
        if not chan:
            return

    @commands.Cog.listener()
    async def on_user_update(self, before: User, after: User):
        for guild in before.mutual_guilds:
            chan: TextChannel = await self.checkLogStatus(guild.id, Logs.USER_UPDATE)
            if not chan:
                return

def setup(bot: commands.Bot):
    bot.add_cog(Logger(bot))
