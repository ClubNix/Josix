import discord
from discord.ext import commands
from discord import ApplicationContext, Member, Interaction, option

import numpy as np

from random import randint

class TTTBtn(discord.ui.Button["TTTView"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: TTTView = self.view

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
            stop = True

        elif view.isFull():
            msg = f"It's a tie !"
            stop = True

        if stop:
            for child in view.children:
                child.disabled = True

            view.stop()

        view.switchPlayer()
        await interaction.response.edit_message(content=msg, view=view)


class TTTView(discord.ui.View):
    children: list[TTTBtn]

    def __init__(self, player1: Member, player2: Member, first: int) -> None:
        super().__init__()

        self.xPlayer, self.oPlayer = (player1, player2) if first else (player2, player1)
        self.currentPlayer = self.xPlayer

        self.state = 0
        self.grid = np.array(
            [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
            ]
        )

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
            col = self.grid[:,i]
            if player == col[0] == col[1] == col[2]:
                return True
        
        if player == self.grid[0,0] == self.grid[1,1] == self.grid[2,2]:
            return True

        if player == self.grid[0,2] == self.grid[1,1] == self.grid[2,0]:
            return True

        return False

    def isFull(self) -> bool:
        return self.grid.all()
        

class TicTacToe(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "games : TicTacToe"

    @commands.slash_command(description="Launch a game of tic-tac-toe")
    @commands.guild_only()
    @option(
        input_type=Member,
        name="opponent",
        description="Mention of your opponent",
        required=True
    )
    async def tic_tac_toe(self, ctx: ApplicationContext, opponent: Member):
        if ctx.author.id == opponent.id:
            await ctx.respond("You can't play against yourself")
            return

        first = randint(0,1)
        await ctx.respond(
            f"Tic Tac Toe : {ctx.author.mention if first else opponent.mention} goes first !",
            view=TTTView(ctx.author, opponent, first)
        )

def setup(bot: commands.Bot):
    bot.add_cog(TicTacToe(bot))