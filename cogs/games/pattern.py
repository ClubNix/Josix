import discord
from discord.ext import commands
from discord import ApplicationContext, Member, Interaction

import numpy as np

from random import randint
from cogs.games.games_base import BaseGame, BaseView
from bot_utils import josix_slash

class PatternBtn(discord.ui.Button["PatternView"]):
    """
    Button for the game Pattern
    Represents a cell in the grid

    Attributes
    ----------
    x : int
        X position of the button
    y : int
        Y position of the button
    label : str
        The label of the button, i.e. its number in the grid
    """

    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.label = (x+1) + 3*y

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: PatternView = self.view

        if not await view.checkGameState():
            return

        if interaction.user.id != view.player.id:
            return

        view.chooseSquare(self.x, self.y)
        view.addMove()
        embed = discord.Embed(
            title=f"Pattern game",
            description="Turn all the squares into blue to win",
            color=0x0089FF
        )
        embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar)
        embed.add_field(name="", value=view)

        if view.checkWin():
            embed.description = f"Congratulations, you won in **{view.count}** moves !"
            view.stopGame()

        await interaction.response.edit_message(embed=embed, view=view)


class PatternView(BaseView):
    """
    View for the game Pattern
    Represents the UI view and game functioning

    Attributes
    ----------
    children : list[PatternBtn]
        All the children of the view
    player : Member
        The user playing the game
    count : int
        Number of plays done by the player
    grid : NDArray
        A 3x3 grid representing game's UI
    """

    children: list[PatternBtn]

    def __init__(
        self,
        interaction: Interaction,
        game: BaseGame,
        idGame: int,
        player: Member
        ) -> None:
        super().__init__(interaction, game, idGame, player)

        self.player = player
        self.count = 0
        self.grid = np.zeros((3,3), dtype=int)

        for x in range(3):
            for y in range(3):
                self.add_item(PatternBtn(x, y))
        self._initGame()

    def _initGame(self) -> None:
        while self.checkWin():
            for _ in range(randint(10, 15)):
                self.chooseSquare(randint(0, 2), randint(0, 2))

    def addMove(self) -> None:
        self.count += 1
    
    def chooseSquare(self, x: int, y: int) -> None:
        tiles = [(x-1,y), (x,y-1), (x,y), (x+1,y), (x,y+1)]
        for tile in tiles:
            j = tile[0]
            i = tile[1]

            if i < 0 or 2 < i or j < 0 or 2 < j:
                continue

            value = self.grid[i][j]
            self.grid[i][j] = 0 if value else 1


    def checkWin(self) -> bool:
        return not self.grid.any()
        
    def __str__(self) -> str:
        res = ""
        for i in self.grid:
            for j in i:
                if j:
                    res += "🟩"
                else:
                    res += "🟦"
            res += "\n"
        return res
        

class Pattern(BaseGame):
    """
    Represents the pattern game extension of the bot

    Attributes
    ----------
    bot : discord.ext.commands.Bot
        The bot that loaded this extension
    """

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__("pattern")
        self.bot = bot
        self.description = "games : pattern"

    @josix_slash(description="Launch a game of tic-tac-toe")
    @commands.guild_only()
    async def pattern_game(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        if self.checkPlayers(ctx.author.id):
            await ctx.respond("You are already in a game. If not, use `/quit_game` command")
            return

        idGame = self.initGame(ctx.author.id)
        view = PatternView(ctx.interaction, self, idGame, ctx.author)
        embed = discord.Embed(
            title=f"Pattern game",
            description="Turn all the squares into blue to win",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.add_field(name="", value=view)
        await ctx.respond(
            embed=embed,
            view=view
        )

def setup(bot: commands.Bot):
    bot.add_cog(Pattern(bot))