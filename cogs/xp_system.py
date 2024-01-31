import discord
from discord.ext import commands
from discord import ApplicationContext, option

import datetime as dt
import logwrite as log

from josix import Josix
from bot_utils import JosixSlash, JosixCog, josix_slash

class XP(JosixCog):
    """
    Represents the XP system extension of the bot

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    """

    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot

    @staticmethod
    def nextLevelXP(lvl: int, xp: int = 0) -> int:
        """
        Calculate the XP needed to get to the next level

        Stolen from MEE6 : https://github.com/Mee6/Mee6-documentation/blob/master/docs/levels_xp.md

        Parameters
        ----------
        lvl : int
            Current level
        xp : int
            XP obtained so far

        Returns
        -------
        int
            The remaining xp needed
        """
        return 5 * (lvl**2) + (50 * lvl) + 100 - xp


    @staticmethod
    def totalLevelXP(lvl: int) -> int:
        """
        Calculate the XP needed to get to reach a level starting from 0

        Stolen from MEE6 : https://github.com/Mee6/Mee6-documentation/blob/master/docs/levels_xp.md

        Parameters
        ----------
        lvl : int
            Current level

        Returns
        -------
        int
            The amount of xp a user needs
        """
        if lvl <= 0:
            return 0

        res = 0
        for i in range(0, lvl):
            res += XP.nextLevelXP(i, 0)
        return res


    async def _updateUser(self, idTarget: int, idGuild: int, xp: int, idCat: int = 0) -> None:
        """
        Updates a user xp and level in the database

        Checks the state of the player then calculate the profits...
        and updates the values

        Parameters
        ----------
        idTarget : int
            ID of the user obtaining XP
        idGuild : int
            ID of the server where the interaction comes from
        xp : int
            The XP the user will obtain
        """
        userDB, guildDB, userGuildDB = self.bot.db.getUserGuildLink(idTarget, idGuild)

        if not userDB:
            self.bot.db.addUser(idTarget)
        if not guildDB:
            self.bot.db.addGuild(idGuild)
            guildDB = self.bot.db.getGuild(idGuild)
        if not userGuildDB:
            self.bot.db.addUserGuild(idTarget, idGuild)
            userGuildDB = self.bot.db.getUserInGuild(idTarget, idGuild)
    
        xpChanId = guildDB.xpNews
        xpEnabled = guildDB.enableXp

        currentXP = userGuildDB.xp
        currentLvl = userGuildDB.lvl
        lastSend = userGuildDB.lastMessage
        userBlocked = userGuildDB.isUserBlocked

        if not xpEnabled or userBlocked:
            return

        if idCat != 0 and idCat in guildDB.blockedCat:
            return

        nowTime = dt.datetime.now()
        if ((nowTime - lastSend).seconds < 60):
            return

        xpNeed = self.nextLevelXP(currentLvl, currentXP - self.totalLevelXP(currentLvl))
        newLvl = xpNeed <= xp

        currentLvl = currentLvl + 1 if newLvl else currentLvl
        currentXP = min(1_899_250, currentXP+xp)

        self.bot.db.updateUserXP(idTarget, idGuild, currentLvl, currentXP, nowTime)

        if newLvl and xpChanId:
            if (xpChan := self.bot.get_channel(xpChanId)) or (xpChan := await self.bot.fetch_channel(xpChanId)):
                await xpChan.send(
                    f"Congratulations <@{idTarget}>, you are now level **{currentLvl}** with **{currentXP}** exp. ! 🎉"
                )


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.process_commands(message)
        if (
            message.author.bot or 
            isinstance(message.channel, discord.DMChannel) or
            isinstance(message.channel, discord.GroupChannel)
        ): return

        idCat = message.channel.category_id
        msgLen = len(message.content)
        xp = 75 if msgLen >= 100 else 50 if msgLen >= 30 else 25

        try:
            await self._updateUser(
                message.author.id,
                message.guild.id,
                xp,
                idCat if idCat else 0
            )
        except Exception as e:
            log.writeError(log.formatError(e))

    @commands.Cog.listener()
    async def on_application_command_completion(self, ctx: ApplicationContext):
        if (
            ctx.author.bot or 
            isinstance(ctx.channel, discord.DMChannel) or
            isinstance(ctx.channel, discord.GroupChannel) or
            not isinstance(ctx.command, JosixSlash)
        ): return

        idCat = ctx.channel.category_id
        cmd: JosixSlash = ctx.command
        if not cmd.give_xp:
            return

        try:
            await self._updateUser(
                ctx.author.id,
                ctx.guild.id,
                25,
                idCat if idCat else 0
            )
        except Exception as e:
            log.writeError(log.formatError(e))


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not (channel := self.bot.get_channel(payload.channel_id)) and not (channel := await self.bot.fetch_channel(payload.channel_id)):
            return

        if (
            payload.member.bot or
            isinstance(channel, discord.DMChannel) or
            isinstance(channel, discord.GroupChannel)
        ): return

        idCat = channel.category_id
        try:
            await self._updateUser(
                payload.user_id,
                payload.guild_id,
                25,
                idCat if idCat else 0
            )
        except Exception as e:
            log.writeError(log.formatError(e))


####################
#
# Commands 
# 
####################


    @staticmethod
    def checkUpdateXP(currentXP: int, amount: int) -> tuple[int, int]:
        """Check the new level and xp after an update and returns these values"""
        newXP = currentXP + amount
        if newXP < 0:
            newXP = 0
        elif newXP > 1_899_250:
            newXP = 1_899_250

        level = 0
        xpNeed = XP.nextLevelXP(level)
        while xpNeed < newXP:
            level += 1
            xpNeed += XP.nextLevelXP(level)

        return newXP, level


    def _xp_update(self, member: discord.Member, amount: int) -> None:
        guild = member.guild
        userDB, guildDB, userGuildDB = self.bot.db.getUserGuildLink(member.id, guild.id)

        if not userDB:
            self.bot.db.addUser(member.id)
        if not guildDB:
            self.bot.db.addGuild(guild.id)
            guildDB = self.bot.db.getGuild(guild.id)
        if not userGuildDB:
            self.bot.db.addUserGuild(member.id, guild.id)
            userGuildDB = self.bot.db.getUserInGuild(member.id, guild.id)

        if userGuildDB.isUserBlocked:
            return

        currentXP = userGuildDB.xp
        newXP, level = self.checkUpdateXP(currentXP, amount)
        self.bot.db.updateUserXP(member.id, guild.id, level, newXP, dt.datetime.now())


    def _lvl_update(self, member: discord.Member, amount: int) -> None:
        guild = member.guild
        userDB, guildDB, userGuildDB = self.bot.db.getUserGuildLink(member.id, guild.id)

        if not userDB:
            self.bot.db.addUser(member.id)
        if not guildDB:
            self.bot.db.addGuild(guild.id)
            guildDB = self.bot.db.getGuild(guild.id)
        if not userGuildDB:
            self.bot.db.addUserGuild(member.id, guild.id)
            userGuildDB = self.bot.db.getUserInGuild(member.id, guild.id)

        if userGuildDB.isUserBlocked:
            return

        currentLvl = userGuildDB.lvl
        newLvl = currentLvl + amount
        if newLvl < 0:
            newLvl = 0
        elif newLvl > 100:
            newLvl = 100

        xp = self.totalLevelXP(newLvl)
        self.bot.db.updateUserXP(member.id, guild.id, newLvl, xp, dt.datetime.now())


    @josix_slash(description="Gives XP to a user")
    @discord.default_permissions(moderate_members=True)
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
            if not self.bot.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._xp_update(member, amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")


    @josix_slash(description="Removes XP to a user")
    @discord.default_permissions(moderate_members=True)
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
            if not self.bot.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._xp_update(member, -amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")


    @josix_slash(description="Gives levels to a user")
    @discord.default_permissions(moderate_members=True)
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
            if not self.bot.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._lvl_update(member, amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")


    @josix_slash(description="Removes levels to a user")
    @discord.default_permissions(moderate_members=True)
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
            if not self.bot.db.getUserInGuild(member.id, ctx.guild.id):
                await ctx.respond("User not registered.")
                return

            self._lvl_update(member, -amount)
        except Exception as e:
            log.writeError(log.formatError(e))

        await ctx.respond("Done !")


    @josix_slash(description="Leaderboard of users based on their xp points in the server")
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
            guildDB = self.bot.db.getGuild(idGuild)
            if not guildDB:
                self.bot.db.addGuild(idGuild)
                await ctx.respond("Server registered now. Try this command later")
                return
            elif not guildDB.enableXp:
                await ctx.respond("The xp system is not enabled in this server.")
                return
            lb = self.bot.db.getXpLeaderboard(idGuild, limit)
        except Exception as e:
            log.writeError(log.formatError(e))

        embed = discord.Embed(
            title="XP Leaderboard",
            description=f"Current leaderboard for the server {ctx.guild.name}",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        if not lb:
            await ctx.respond(embed=embed)
            return

        count = 0
        nbFields = 0
        res = ""
        for i, row in enumerate(lb):
            idUser, xp = row.idUser, row.xp
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


    @josix_slash(description="Show the XP card of the user")
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
        stats = self.bot.db.getUserInGuild(member.id, idGuild)
        if not stats:
            await ctx.respond("This user is not registered")
            return

        xp, lvl = stats.xp, stats.lvl
        lastNeed = self.totalLevelXP(lvl)
        xpNeed = lastNeed + self.nextLevelXP(lvl, 0)
        nextXp = self.nextLevelXP(lvl, xp-lastNeed)
        progress = round((xp / xpNeed) * 100, 2)
        pos = self.bot.db.getLeaderboardPos(member.id, idGuild)

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
            f"`Leaderboard` : **{'?' if pos is None else pos}**"
        )))
        await ctx.respond(embed=embed)


    @josix_slash(description="Block or unblock xp progression for a member")
    @discord.default_permissions(moderate_members=True)
    @commands.guild_only()
    @option(
        input_type=discord.Member,
        name="member",
        description="Mention of the targeted user",
        required=True
    )
    async def block_user_xp(self, ctx: ApplicationContext, member: discord.Member):
        await ctx.defer(ephemeral=False, invisible=False)
        if member.bot:
            await ctx.respond("You can't perform this action on a bot")
            return

        idTarget = member.id
        idGuild = ctx.guild_id
        
        userDB, guildDB, userGuildDB = self.bot.db.getUserGuildLink(idTarget, idGuild)

        if not userDB:
            self.bot.db.addUser(idTarget)
        if not guildDB:
            self.bot.db.addGuild(idGuild)
        if not userGuildDB:
            self.bot.db.addUserGuild(idTarget, idGuild)
            userGuildDB = self.bot.db.getUserInGuild(idTarget, idGuild)

        blocked = userGuildDB.isUserBlocked
        self.bot.db.updateUserBlock(idTarget, idGuild)
        await ctx.respond(f"The block status for {member.mention} is set to **{not blocked}**")


def setup(bot: commands.Bot):
    bot.add_cog(XP(bot, True))