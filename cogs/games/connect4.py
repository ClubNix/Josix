import discord
from discord.ext import commands
from discord import ApplicationContext, Interaction, option

import numpy as np

from random import randint
from cogs.games.games_base import BaseGame, BaseView
from bot_utils import josix_slash

class C4Button(discord.ui.Button["C4View"]):
    """
    Button for the game Connect-4
    Represents the column number where the user place its token

    Attributes
    ----------
    x : int
        Column number
    label : str
        Button label, i.e. its column number
        
    """

    def __init__(self, x: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b")
        self.x = x
        self.label = x+1

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: C4View = self.view

        if not await view.checkGameState():
            return

        if interaction.user.id != view.currentPlayer.id:
            return

        if not view.checkCol(self.x):
            self.disabled = True
            return

        y = view.addToken(self.x)
        
        if view.checkWin(self.x, y):
            view.stopGame()
            desc = f"{view.currentPlayer.name} won !"
            if not interaction.guild: return
            view.game.grantsXP(view.currentPlayer, interaction.guild, 50)

        elif view.isFull():
            view.stopGame()
            desc = "It's a tie !",

        else:
            if not view.checkCol(self.x):
                self.disabled = True
            view.switchPlayer()
            desc = f"{view.currentPlayer.name}'s turn"

        embed = discord.Embed(
            title="Connect 4 Game",
            description=desc,
            color=0x0089FF
        )
        embed.add_field(name="", value=view)
        await interaction.response.edit_message(embed=embed, view=view)
        

class C4View(BaseView):
    """
    View for the game Connect-4
    Represents the UI view and game functioning

    Attributes
    ----------
    children : list[C4Button]
        All the children of the view
    redPlayer : Member
        The player of the red tokens
    yellowPlayer : Member
        The player of the yellow tokens
    currentPlayer : Member
        The user currently playing
    grid : NDArray
        A 6x7 grid representing the game's UI (the board)
    """

    children: list[C4Button]
    def __init__(
        self,
        interaction: Interaction,
        game: BaseGame,
        idGame: int,
        player1: discord.Member,
        player2: discord.Member,
        first: int
        ):
        super().__init__(interaction, game, idGame, player1)
        self.redPlayer, self.yellowPlayer = (player1, player2) if first else (player2, player1)
        self.currentPlayer = self.redPlayer

        self.grid = np.zeros((6, 7))

        for i in range(7):
            self.add_item(C4Button(i))


    def addToken(self, x: int) -> int:
        for i in range(6):
            if self.grid[5-i][x] == 0:
                self.grid[5-i][x] = 1 if self.currentPlayer.id == self.redPlayer.id else 2
                return 5-i
        return -1

    def switchPlayer(self):
        self.currentPlayer = self.redPlayer if self.currentPlayer.id == self.yellowPlayer.id else self.yellowPlayer

    def checkCol(self, x: int) -> bool:
        return self.grid[0][x] == 0

    def isFull(self) -> bool:
        return self.grid.all()

    def checkWin(self, x: int, y: int) -> bool:
        if x < 0 or 6 < x or y < 0 or 5 < y:
            return False
        
        token = self.grid[y][x]
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                count = 0
                if cell != token:
                    continue

                count = 1
                for testX in range(1, 4):
                    if (j + testX > 6) or (row[j + testX] != token):
                        count = 1
                        break
                    count += 1
                    if count == 4:
                        return True

                for testY in range(1, 4):
                    if (i + testY > 5) or (self.grid[i + testY][j] != token):
                        count = 1
                        break
                    count += 1
                    if count == 4:
                        return True

                for testDiag in range(1, 4):
                    if (i + testDiag > 5) or (j + testDiag > 6) or (self.grid[i+testDiag][j+testDiag] != token):
                        count = 1
                        break
                    count += 1
                    if count == 4:
                        return True

        return False


    def __str__(self) -> str:
        res = ""
        for i in self.grid:
            res += "|"
            for j in i:
                res += "⚫" if j == 0 else "🔴" if j == 1 else "🟡"
                res += "|"
            res += "\n"
        res += "**‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾**"
        return res


class Connect4(BaseGame):
    """
    Represents the Connect-4 game extension of the bot

    Attributes
    ----------
    bot : discord.ext.commands.Bot
        The bot that loaded this extension
    """

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__("connect4")
        self.bot = bot
        self.description = "games : Connect 4"

    @josix_slash(description="Launch a game of Connect 4", give_xp=True)
    @option(
        input_type=discord.Member,
        name="opponent",
        description="Mention of your opponent",
        required=True
    )
    async def connect4(self, ctx: ApplicationContext, opponent: discord.Member):
        await ctx.defer(ephemeral=False, invisible=False)
        if ctx.author.id == opponent.id:
            await ctx.respond("You can't challenge yourself")
            return

        if self.checkPlayers(ctx.author.id, opponent.id):
            await ctx.respond("One of the players is already in a game. If not, use `/quit_game` command")
            return

        idGame = self.initGame(ctx.author.id, opponent.id)
        first = randint(0, 1)
        view = C4View(ctx.interaction, self, idGame, ctx.author, opponent, first)
        embed = discord.Embed(
            title="Connect 4 Game",
            description=f"{view.currentPlayer.name}'s turn",
            color=0x0089FF
        )
        embed.add_field(name="", value=view)
        await ctx.respond(embed=embed, view=view)
        


def setup(bot: commands.Bot):
    bot.add_cog(Connect4(bot))