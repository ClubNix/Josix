import discord
from discord.ext import commands

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

def setup(bot: commands.Bot):
    bot.add_cog(XP(bot))