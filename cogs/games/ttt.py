from random import randint

import discord
from discord import ApplicationContext, Interaction, Member, option
from discord.ext import commands

from cogs.games.games_base import BaseGame, BaseView
from josix import Josix
from pkg.bot_utils import josix_slash


class TTTBtn(discord.ui.Button["TTTView"]):
    """
    Button for the game TicTacToe
    Represents a cell in the 3x3 grid of the game

    Attributes
    ----------
    x : int
        X position of the button
    y : int
        Y position of the button
    """

    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: TTTView = self.view

        if not (
            await view.checkGameState() and
            interaction.user 
        ):
            return

        if view.grid[self.x][self.y]:
            return

        if interaction.user.id != view.currentPlayer.id:
            return

        player = view.currentPlayer
        value = 1 if player.id == view.xPlayer.id else 2
        msg = ""
        stop = False

        if value == 1:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            msg = f"It's {view.oPlayer.mention} turn !"

        elif value == 2:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            msg = f"It's {view.xPlayer.mention} turn !"

        view.grid[self.x][self.y] = value
        self.disabled = True

        if view.checkWin():
            msg = f"{view.currentPlayer.mention} won !"
            if not interaction.guild:
                return
            view.game.grantsXP(view.currentPlayer, interaction.guild, 10)
            stop = True

        elif view.isFull():
            msg = "It's a tie !"
            stop = True

        if stop:
            view.stopGame()

        view.switchPlayer()
        await interaction.response.edit_message(content=msg, view=view)


class TTTView(BaseView):
    """
    View for the game TicTacToe
    Represents the UI view and game functioning

    Attributes
    ----------
    children : list[TTTBtn]
        All the children of the view
    xPlayer : Member
        The player for the 'X'
    oPlayer : Member
        The player for the 'O'
    state : int
        The state of the game
    grid : NDArray
        A 3x3 grid representing game's UI
    """

    children: list[TTTBtn] # type: ignore

    def __init__(
        self,
        interaction: Interaction,
        game: BaseGame,
        idGame: int,
        player1: Member,
        player2: Member,
        first: int
        ) -> None:
        super().__init__(interaction, game, idGame, player1)

        self.xPlayer, self.oPlayer = (player1, player2) if first else (player2, player1)
        self.currentPlayer = self.xPlayer

        self.grid = [[0 for x in range(3)] for y in range(3)]
        for x in range(3):
            for y in range(3):
                self.add_item(TTTBtn(x, y))

    def switchPlayer(self):
        self.currentPlayer = self.xPlayer if self.currentPlayer.id == self.oPlayer.id else self.oPlayer

    def checkWin(self) -> bool:
        player = 1 if self.currentPlayer == self.xPlayer else 2

        for row in self.grid:
            if player == row[0] == row[1] == row[2]:
                return True

        for i in range(3):
            col = [row[i] for row in self.grid]
            if player == col[0] == col[1] == col[2]:
                return True
        
        if player == self.grid[0][0] == self.grid[1][1] == self.grid[2][2]:
            return True

        if player == self.grid[0][2] == self.grid[1][1] == self.grid[2][0]:
            return True

        return False

    def isFull(self) -> bool:
        for i in self.grid:
            for j in i:
                if j == 0:
                    return False
        return True
        

class TicTacToe(BaseGame):
    """
    Represents the Tic-Tac-Toe game extension of the bot

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    """

    def __init__(self, bot: Josix) -> None:
        super().__init__("tic-tac-toe", bot.db)
        self.bot = bot
        self.description = "games : TicTacToe"

    @josix_slash(description="Launch a game of tic-tac-toe", give_xp=True)
    @commands.guild_only()
    @option(
        input_type=Member,
        name="opponent",
        description="Mention of your opponent",
        required=True
    )
    async def tic_tac_toe(self, ctx: ApplicationContext, opponent: Member):
        await ctx.defer(ephemeral=False, invisible=False)
        if ctx.author.id == opponent.id:
            await ctx.respond("You can't play against yourself")
            return

        if self.checkPlayers(ctx.author.id, opponent.id):
            await ctx.respond("One of the players is already in a game. If not use `/quit_game` command")
            return

        first = randint(0,1)
        idGame = self.initGame(ctx.author.id, opponent.id)
        await ctx.respond(
            f"Tic Tac Toe : {ctx.author.mention if first else opponent.mention} goes first !",
            view=TTTView(ctx.interaction, self, idGame, ctx.author, opponent, first)
        )

def setup(bot: Josix):
    bot.add_cog(TicTacToe(bot))