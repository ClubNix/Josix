import discord
from discord.ext import commands
from discord import ApplicationContext, option

import datetime as dt
import os

from database.database import DatabaseHandler

class XP(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseHandler(os.path.basename(__file__))

    def nextLevelXP(self, lvl: int, xp: int) -> int:
        """Stolen from MEE6 : https://github.com/Mee6/Mee6-documentation/blob/master/docs/levels_xp.md """
        return 5 * (lvl**2) + (50 * lvl) + 100 - xp

    def totalLevelXP(self, lvl: int) -> int:
        if lvl <= 0:
            return 0

        res = 0
        for i in range(1, lvl+1):
            res += self.nextLevelXP(i, res)
        return res

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.process_commands(message)
        if message.author.bot:
            return

        auth = message.author
        guild = message.guild
        userDB, guildDB, userGuildDB = self.db.getXPUtils(auth.id, guild.id)

        if not userDB:
            self.db.addUser(auth.id)
        if not guildDB:
            self.db.addGuild(guild.id)
            guildDB = self.db.getGuildXP(guild.id)
        if not userGuildDB:
            self.db.addUserGuild(auth.id, guild.id)
            userGuildDB = self.db.getUserGuildXP(auth.id, guild.id)
    
        xpChanId: int = guildDB[0]
        xpEnabled: bool = guildDB[1]

        currentXP: int = userGuildDB[0]
        currentLvl: int = userGuildDB[1]
        lastSend: dt.datetime = userGuildDB[2]

        if not xpEnabled:
            return

        nowTime = dt.datetime.now()
        if (nowTime - lastSend).seconds < 60:
            return

        msgLen = len(message.content)
        xp = 100 if msgLen >= 75 else 50 if msgLen >= 20 else 25

        xpNeed = self.nextLevelXP(currentLvl, currentXP - self.totalLevelXP(currentLvl))
        newLvl = xpNeed < (currentXP + xp)

        currentLvl = currentLvl + 1 if newLvl else currentLvl
        currentXP += xp
        self.db.updateUserXP(auth.id, guild.id, currentLvl, currentXP, nowTime)

        if newLvl and xpChanId:
            xpChan = self.bot.get_channel(xpChanId)
            if xpChan:
                await xpChan.send(
                    f"Congratulations {auth.mention}, you are now level **{currentLvl}** with **{currentXP}** exp ! 🎉"
                )


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

        currentXP: int = userGuildDB[0]

        newXP = currentXP + amount
        if newXP < 0:
            newXP = 0
        elif newXP > 1_899_250:
            newXP = 1_899_250

        xpNeed = self.nextLevelXP(0, 0)
        level = 0
        while xpNeed < newXP:
            level += 1
            xpNeed += self.nextLevelXP(level, xpNeed)
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

        currentLvl: int = userGuildDB[1]
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

        if not self.db.getUserInGuild(member.id, ctx.guild.id):
            await ctx.respond("User not registered.")
            return

        self._xp_update(member, amount)
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

        if not self.db.getUserInGuild(member.id, ctx.guild.id):
            await ctx.respond("User not registered.")
            return

        self._xp_update(member, -amount)
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

        if not self.db.getUserInGuild(member.id, ctx.guild.id):
            await ctx.respond("User not registered.")
            return

        self._xp_update(member, amount)
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

        if not self.db.getUserInGuild(member.id, ctx.guild.id):
            await ctx.respond("User not registered.")
            return

        self._xp_update(member, -amount)
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

        guildDB = self.db.getGuildXP(idGuild)
        if not guildDB:
            self.db.addGuild(idGuild)
            await ctx.respond("Server registered now. Try this command later")
            return
        elif not guildDB[1]:
            await ctx.respond("The xp system is not enabled in this server.")
            return

        embed = discord.Embed(
            title="XP Leaderboard",
            description=f"Current leaderboard for the server {ctx.guild.name}",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.set_thumbnail(url=self.bot.user.display_avatar)

        lb = self.db.getXpLeaderboard(idGuild, limit)
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
            if nbFields > 25:
                break
            
            res += text
            count += len(text)
        if len(text) > 0:
            embed.append_field(
                discord.EmbedField(name="", value=res)
            )
        await ctx.respond(embed=embed)




def setup(bot: commands.Bot):
    bot.add_cog(XP(bot))