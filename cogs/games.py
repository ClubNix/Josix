import discord
from discord.ext import commands

from asyncio import TimeoutError
from database.database import DatabaseHandler

class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()

    def updateElo(self, oldElo: int, foeElo: int, win: bool):
        """
        Elo calculations from Pokemon Showdown 
        - https://github.com/smogon/pokemon-showdown/blob/master/server/ladders-remote.ts
        - https://github.com/smogon/pokemon-showdown/blob/master/server/ladders-local.ts
        - https://en.wikipedia.org/wiki/Elo_rating_system
        """

        k = 50

        # dynamic K-scaling (optional)
        if oldElo < 1100:
            if win:
                k = 80 - (oldElo - 1000) * 30 / 100
            else:
                k = 20 + (oldElo - 1000) * 30 / 100
        elif (oldElo > 1350 and oldElo <= 1600):
            k = 40

        # Main elo formula
        e = 1 / (1 + pow(10, (foeElo - oldElo) / 400))

        modifier = (k * ((1 if win else 0) - e))
        if modifier < -40:
            modifier = -40
        elif modifier > 40:
            modifier = 40

        newElo = int(oldElo + modifier)
        return max(newElo, 1000)

    def updateFoes(self, foes: tuple[discord.User], eloList: list, winnerElo: int) -> str:
        text = ""
        for i, foe in enumerate(foes):
            newElo = self.updateElo(eloList[i], winnerElo, False)
            text += f"{foe.mention} : {eloList[i]} - {eloList[i] - newElo} -> **{newElo}**\n"
            self.db.updatePlayerStat(foe.id, newElo)
        return text


    ### Old command not updated because we don't have our dart game anymore
    @commands.command(description="Add the results of your dart game in the database", aliases=["DART"])
    async def dart(self, ctx: commands.Context, winner: discord.User, *foes: discord.User):
        """
        Command to update scores after a dart match
        Take as first parameter the winner (@...#xxxx)
        Take as second parameter, as many users as you want, all considered as loosers

        The command is currently disabled
        """

        def checkReact(reaction : discord.Reaction, user : discord.User):
            return user in foes and reaction.emoji == "✅" and self.bot != user
        
        if winner in foes:
            await ctx.send("You can't challenge yourself !")
            return

        eloList = []
        for foe in foes:
            playerStat = self.db.getPlayerStat(foe.id)
            if not playerStat:
                eloList.append(1000)
                self.db.addUser(foe.id)
            else:
                eloList.append(playerStat[0])
        foesElo = sum((eloList)) / len(eloList)

        player1 = self.db.getPlayerStat(winner.id)
        if not player1:
            self.db.addUser(winner.id)
            elo1 = 1000
        else:
            elo1 = player1[0]

        text = ""
        for foe in foes:
            text += foe.mention + ", "
        text = text[0:len(text)-2]
        text += f"\nYou have been signed as loser(s) in a dart game against {winner.mention}. "
        text += "I need at least one approval from one of you, just react with :white_check_mark: on this message"

        msg : discord.Message = await ctx.send(text)
        await msg.add_reaction("✅")

        try:
            await self.bot.wait_for("reaction_add", check=checkReact, timeout=60) 
        except TimeoutError as _:
            await ctx.send("Nobody approved this game, no updates have been done")
            await msg.delete()
            return

        newElo1 = self.updateElo(elo1, foesElo, True)
        self.db.updatePlayerStat(winner.id, newElo1)
        text = self.updateFoes(foes, eloList, elo1)
        self.db.addDartLog(ctx.guild.id, winner, foes)

        embed = discord.Embed(title="Dart Game", description="Results of last dart game", color=0x0089FF)
        embed.set_author(name=ctx.author)
        embed.set_thumbnail(url=(ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar))
        embed.add_field(name="Winner", value=f"{winner.mention} : {elo1} + {newElo1 - elo1} -> **{newElo1}**", inline=False)
        embed.add_field(name="Loser(s)", value=text)
        await ctx.send(embed=embed)
        

def setup(bot: commands.Bot):
    bot.add_cog(Games(bot))