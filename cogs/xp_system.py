import discord
from discord.ext import commands
from discord import ApplicationContext, option

import datetime as dt
import logwrite as log
import os

from database.database import DatabaseHandler

class XP(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

    def nextLevelXP(self, lvl: int, xp: int = 0) -> int:
        """Stolen from MEE6 : https://github.com/Mee6/Mee6-documentation/blob/master/docs/levels_xp.md """
        return 5 * (lvl**2) + (50 * lvl) + 100 - xp

    def totalLevelXP(self, lvl: int) -> int:
        if lvl <= 0:
            return 0

        res = 0
        for i in range(0, lvl):
            res += self.nextLevelXP(i, 0)
        return res

    async def _updateUser(self, idTarget: int, idGuild: int, xp: int):
        userDB, guildDB, userGuildDB = self.db.getXPUtils(idTarget, idGuild)

        if not userDB:
            self.db.addUser(idTarget)
        if not guildDB:
            self.db.addGuild(idGuild)
            guildDB = self.db.getGuildXP(idGuild)
        if not userGuildDB:
            self.db.addUserGuild(idTarget, idGuild)
            userGuildDB = self.db.getUserGuildXP(idTarget, idGuild)
    
        xpChanId = guildDB[0]
        xpEnabled = guildDB[1]

        currentXP = userGuildDB[0]
        currentLvl = userGuildDB[1]
        lastSend = userGuildDB[2]

        if not xpEnabled:
            return

        nowTime = dt.datetime.now()
        if ((nowTime - lastSend).seconds < 60):
            return

        xpNeed = self.nextLevelXP(currentLvl, currentXP - self.totalLevelXP(currentLvl))
        newLvl = xpNeed <= xp

        currentLvl = currentLvl + 1 if newLvl else currentLvl
        currentXP = min(1_899_250, currentXP+xp)

        self.db.updateUserXP(idTarget, idGuild, currentLvl, currentXP, nowTime)

        if newLvl and xpChanId:
            xpChan = self.bot.get_channel(xpChanId)
            if xpChan:
                await xpChan.send(
                    f"Congratulations <@{idTarget}>, you are now level **{currentLvl}** with **{currentXP}** exp. ! 🎉"
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.process_commands(message)
        if message.author.bot:
            return

        msgLen = len(message.content)
        xp = 100 if msgLen >= 75 else 50 if msgLen >= 20 else 25
        try:
            await self._updateUser(
                message.author.id,
                message.guild.id,
                xp
            )
        except Exception as e:
            log.writeError(log.formatError(e))

    @commands.Cog.listener()
    async def on_application_command_completion(self, ctx: ApplicationContext):
        if ctx.author.bot:
            return

        try:
            await self._updateUser(
                ctx.author.id,
                ctx.guild.id,
                50
            )
        except Exception as e:
            log.writeError(log.formatError(e))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return

        try:
            await self._updateUser(
                payload.user_id,
                payload.guild_id,
                25
            )
        except Exception as e:
            log.writeError(log.formatError(e))


####################
#
# Commands 
# 
####################


    def _xp_update(self, member: discord.Member, amount: int) -> None:
        guild = member.guild
        userDB, guildDB, userGuildDB = self.db.getXPUtils(member.id, guild.id)

        if not userDB:
            self.db.addUser(member.id)
        if not guildDB:
            self.db.addGuild(guild.id)
            guildDB = self.db.getGuildXP(guild.id)
        if not userGuildDB:
            self.db.addUserGuild(member.id, guild.id)
            userGuildDB = self.db.getUserGuildXP(member.id, guild.id)

        currentXP = userGuildDB[0]

        newXP = currentXP + amount
        print(newXP, currentXP, amount)
        if newXP < 0:
            newXP = 0
        elif newXP > 1_899_250:
            newXP = 1_899_250

        level = 0
        xpNeed = self.nextLevelXP(level)
        while xpNeed < newXP:
            level += 1
            xpNeed += self.nextLevelXP(level)

        self.db.updateUserXP(member.id, guild.id, level, newXP, dt.datetime.now())

    def _lvl_update(self, member: discord.Member, amount: int) -> None:
        guild = member.guild
        userDB, guildDB, userGuildDB = self.db.getXPUtils(member.id, guild.id)

        if not userDB:
            self.db.addUser(member.id)
        if not guildDB:
            self.db.addGuild(guild.id)
            guildDB = self.db.getGuildXP(guild.id)
        if not userGuildDB:
            self.db.addUserGuild(member.id, guild.id)
            userGuildDB = self.db.getUserGuildXP(member.id, guild.id)

        currentLvl = userGuildDB[1]
        newLvl = currentLvl + amount
        if newLvl < 0:
            newLvl = 0
        elif newLvl > 100:
            newLvl = 100

        xp = self.totalLevelXP(newLvl)
        self.db.updateUserXP(member.id, guild.id, newLvl, xp, dt.datetime.now())

    @commands.slash_command(description="Gives XP to a user")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    @option(
        input_type=discord.Member,
        name="member",
        description="Mention of the target member",
        required=True
    )
    @option(
        input_type=int,
        name="amount",
        description="The amount of XP to give",
        min_value=1,
        required=True
    )
    async def give_xp(self, ctx: ApplicationContext, member: discord.Member, amount: int):
        await ctx.defer(ephemeral=False, invisible=False)
        if member.bot:
            await ctx.respond("You can't edit a bot's xp !")
            return

        try:
            if not self.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._xp_update(member, amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")

    @commands.slash_command(description="Removes XP to a user")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    @option(
        input_type=discord.Member,
        name="member",
        description="Mention of the target member",
        required=True
    )
    @option(
        input_type=int,
        name="amount",
        description="The amount of XP to remove",
        min_value=1,
        required=True
    )
    async def remove_xp(self, ctx: ApplicationContext, member: discord.Member, amount: int):
        await ctx.defer(ephemeral=False, invisible=False)
        if member.bot:
            await ctx.respond("You can't edit a bot's xp !")
            return

        try:
            if not self.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._xp_update(member, -amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")

    @commands.slash_command(description="Gives levels to a user")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    @option(
        input_type=discord.Member,
        name="member",
        description="Mention of the target member",
        required=True
    )
    @option(
        input_type=int,
        name="amount",
        description="The amount of levels to give",
        min_value=1,
        required=True
    )
    async def give_levels(self, ctx: ApplicationContext, member: discord.Member, amount: int):
        await ctx.defer(ephemeral=False, invisible=False)
        if member.bot:
            await ctx.respond("You can't edit a bot's levels !")
            return

        try:
            if not self.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._lvl_update(member, amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")

    @commands.slash_command(description="Removes levels to a user")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    @option(
        input_type=discord.Member,
        name="member",
        description="Mention of the target member",
        required=True
    )
    @option(
        input_type=int,
        name="amount",
        description="The amount of levels to remove",
        min_value=1,
        required=True
    )
    async def remove_levels(self, ctx: ApplicationContext, member: discord.Member, amount: int):
        await ctx.defer(ephemeral=False, invisible=False)
        if member.bot:
            await ctx.respond("You can't edit a bot's levels !")
            return

        try:
            if not self.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._lvl_update(member, -amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")


    @commands.slash_command(description="Leaderboard of users based on their xp points in the server")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    @option(
        input_type=int,
        name="limit",
        description="Limit of users in the leaderboard (default 10)",
        default=10,
        min_value=1,
        max_value=50
    )
    async def leaderboard(self, ctx: ApplicationContext, limit: int):
        await ctx.defer(ephemeral=False, invisible=False)
        idGuild = ctx.guild.id

        try:
            guildDB = self.db.getGuildXP(idGuild)
            if not guildDB:
                self.db.addGuild(idGuild)
                await ctx.respond("Server registered now. Try this command later")
                return
            elif not guildDB[1]:
                await ctx.respond("The xp system is not enabled in this server.")
                return
            lb = self.db.getXpLeaderboard(idGuild, limit)
        except Exception as e:
            log.writeError(log.formatError(e))

        embed = discord.Embed(
            title="XP Leaderboard",
            description=f"Current leaderboard for the server {ctx.guild.name}",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.set_thumbnail(url=self.bot.user.display_avatar)

        count = 0
        nbFields = 0
        res = ""
        for i, row in enumerate(lb):
            idUser, xp, _ = row
            text = f"**{i+1}** - <@{idUser}> ({xp})\n"
            if len(text) + count > 1024:
                embed.append_field(
                    discord.EmbedField(name="", value=res)
                )
                count = 0
                nbFields += 1
                res = ""
            if nbFields == 25:
                break
            
            res += text
            count += len(text)
        if len(text) > 0 and nbFields < 25:
            embed.append_field(
                discord.EmbedField(name="", value=res)
            )
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Show the XP card of the user")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    @option(
        input_type=discord.Member,
        name="member",
        description="Mention of the target member",
        default=None
    )
    async def profile(self, ctx: ApplicationContext, member: discord.Member):
        await ctx.defer(ephemeral=False, invisible=False)
        if not member:
            member = ctx.author

        if member.bot:
            await ctx.respond("You can't use this command on a bot user.")
            return

        idGuild = ctx.guild.id
        stats = self.db.safeExecute(self.db.getUserGuildXP, member.id, idGuild)
        if not stats:
            await ctx.respond("This user is not registered")
            return

        xp: int
        lvl: int
        xp, lvl, _ = stats
        lastNeed = self.totalLevelXP(lvl)
        xpNeed = lastNeed + self.nextLevelXP(lvl, 0)
        nextXp = self.nextLevelXP(lvl, xp-lastNeed)
        progress = round((xp / xpNeed) * 100, 2)
        pos = self.db.safeExecute(self.db.getLeaderboardPos, member.id, idGuild)

        embed = discord.Embed(
            title=f"{member}'s card",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.set_thumbnail(url=member.display_avatar)
        embed.add_field(name="", value="\n".join((
            f"`XP` : **{xp}**",
            f"`Level` : **{lvl}**",
            f"`Progress` : **{progress}%**"
        )))
        embed.add_field(name="", value="\n".join((
            f"`Next Level XP` : **{nextXp}**",
            f"`Total XP needed` : **{xpNeed}**",
            f"`Leaderboard` : **{pos[0] if pos else '?'}**"
        )))
        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(XP(bot))