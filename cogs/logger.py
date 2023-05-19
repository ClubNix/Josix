import discord
from discord.ext import commands
from discord.ui.select import Select
from discord import AutoModRule, AutoModActionExecutionEvent, AutoModAction, TextChannel

from database.database import DatabaseHandler
from enum import IntEnum

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
    USER_UPDATE = 12


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
        chan: TextChannel = self.checkLogStatus(payload.guild_id)
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
        if len(payload.content) < 1024: embed.add_field(name="Content", value=payload.content, inline=False)
        await chan.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Logger(bot))
