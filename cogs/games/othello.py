import discord
from discord.ext import commands
from discord import ApplicationContext, Interaction, SelectOption, option

import numpy as np

from random import randint
from cogs.games.games_base import BaseGame, BaseView
from bot_utils import josix_slash


class OthelloInput(discord.ui.Select):
    """
    Input for the game Othello
    Represents the input for the game
        - Letter A - H for rows
        - Number of 1 - 8 for columns
    """

    def __init__(self, custom_id: str, placeholder: str, options: list[SelectOption]):
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            options=options,
            select_type=discord.ComponentType.string_select,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: OthelloView = self.view

        if not await view.checkGameState():
            return

        if interaction.user.id != view.currentPlayer.id:
            return

        oldEmbed = interaction.message.embeds[0]
        value = 1 if view.currentPlayer.id == view.whitePlayer.id else 2
        optionValue = 0
        try:
            optionValue = int(interaction.data["values"][0])
        except KeyError:
            return

        if self.custom_id == "row":
            view.setYMove(optionValue)
        elif self.custom_id == "col":
            view.setXMove(optionValue)

        self.disabled = True
        self.placeholder = self.options[optionValue].label
        for child in view.children:
            if not child.disabled:
                await interaction.response.edit_message(embed=oldEmbed, view=view)
                return

        if not view.checkPlay(view.xMove, view.yMove, value):
            view.enable_all_items()
            await interaction.response.edit_message(embed=oldEmbed, view=view)
            return

        view.addToken(view.xMove, view.yMove)
        view.switchTokens(view.getSwitches(value, view.xMove, view.yMove))

        if view.isEnded():
            winner = view.checkWinner()
            view.stopGame()
            if not winner:
                desc = "It's a tie !"
            else:
                desc = f"{winner.mention} won !"

        else:
            view.enable_all_items()
            if view.canPlay(view.whitePlayer if view.currentPlayer.id == view.blackPlayer.id else view.blackPlayer):
                view.switchPlayer()
            desc = f"{view.currentPlayer.mention}'s turn !"

        embed = discord.Embed(
            title="Othello Game",
            description=desc,
            color=0x0089FF
        )
        embed.add_field(name="", value=view)
        await interaction.response.edit_message(embed=embed, view=view)


class OthelloView(BaseView):
    """
    View for the game TicTacToe
    Represents the UI view and game functioning

    Attributes
    ----------
    children : list[OthelloInput]
        All the children of the view
    __directions : list[tuple[int, int]]
        All the possible directions
    whitePlayer : Member
        Player who use white tokens
    blackPlayer : Member
        Player who use black tokens
    grid : NDArray
        A 8x8 grid representing the game's UI (the board)
    xMove : int
        X value of the move chose by the player
    yMove : int
        Y value of the move chose by the player
    """

    children: list[OthelloInput]
    __directions = [(0,-1), (0,1), (-1,0), (1, 0), (-1,-1), (1,-1), (-1,1), (1,1)]
    
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

        self.whitePlayer, self.blackPlayer = (player1, player2) if first else (player2, player1)
        self.currentPlayer = self.whitePlayer
        self.grid = np.zeros((8, 8), dtype=int)
        self.xMove = -1
        self.yMove = -1

        self.add_item(OthelloInput(
            "row",
            "A",
            [SelectOption(
                label=chr(ord("A")+i),
                value=str(i)
            ) for i in range(8)]
        ))
        self.add_item(OthelloInput(
            "col",
            "1",
            [SelectOption(
                label=str(i+1),
                value=str(i)
            ) for i in range(8)]
        ))
        self._initGrid()

    def _initGrid(self):
        self.grid[3][3] = 1
        self.grid[4][4] = 1
        self.grid[3][4] = 2
        self.grid[4][3] = 2

    def getSwitches(self, value: int, x: int, y: int) -> list[tuple[int, int]]:
        tokens = []
        for direction in self.__directions:
            offX, offY = direction
            i, j = y+offY, x+offX
            isClosed = False
            tmpTokens = []
            while (0 <= i and i <= 7) and (0 <= j and j <= 7) and not isClosed:
                if self.grid[i][j] == 0:
                    break
                elif self.grid[i][j] == value:
                    isClosed = True
                else:
                    tmpTokens.append((j,i))
                i += offY
                j += offX
            
            if isClosed:
                tokens.extend(tmpTokens)
        return tokens

    def checkCell(self, x: int, y: int) -> bool:
        return self.grid[y][x] == 0

    def checkPlay(self, x: int, y: int, value: int) -> bool:
        oppoV = 1 if value == 2 else 2
        if not self.checkCell(x, y):
            return False
        elif y - 1 >= 0 and self.grid[y-1][x] == oppoV:
            return True
        elif y + 1 <= 7 and self.grid[y+1][x] == oppoV:
            return True
        elif x - 1 >= 0 and self.grid[y][x-1] == oppoV:
            return True
        elif x + 1 <= 7 and self.grid[y][x+1] == oppoV:
            return True
        else:
            return False

    def isEnded(self) -> bool:
        return self.grid.all() or not (self.canPlay(self.whitePlayer) or self.canPlay(self.blackPlayer))

    def canPlay(self, player: discord.Member) -> bool:
        value = 1 if self.currentPlayer.id == player.id else 2
        for i, row in enumerate(self.grid):
            for j in range(len(row)):
                if not self.checkPlay(j, i, value):
                    continue

                if len(self.getSwitches(value, j, i)) > 0:
                    return True
        return False

    def checkWinner(self) -> discord.Member | None:
        whitePoints = 0
        blackPoints = 0
        for i in self.grid:
            for j in i:
                if j == 1:
                    whitePoints += 1
                elif j == 2:
                    blackPoints += 1
        
        if whitePoints == blackPoints:
            return None

        return self.whitePlayer if whitePoints > blackPoints else self.blackPlayer

    def addToken(self, x: int, y: int) -> int:
        self.grid[y][x] = 1 if self.currentPlayer.id == self.whitePlayer.id else 2

    def setXMove(self, x: int) -> None:
        self.xMove = x
    
    def setYMove(self, y: int) -> None:
        self.yMove = y

    def switchPlayer(self) -> None:
        self.currentPlayer = self.whitePlayer if self.currentPlayer.id == self.blackPlayer.id else self.blackPlayer

    def switchTokens(self, tokens: list[tuple[int, int]]) -> None:
        for coords in tokens:
            x,y = coords
            self.grid[y, x] = 1 if self.grid[y, x] == 2 else 2


    def __str__(self) -> str:
        res = ""
        for i in range(1, 9):
            res += f" **{i}**"
        res += "\n**\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_**\n"
        for i, row in enumerate(self.grid):
            res += "**|** "
            for cell in row:
                res += "🟢" if cell == 0 else "⚪" if cell == 1 else "⚫"
            res += " **|** **" + chr(ord("A") + i) + "**\n"
        res += "**‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾**\n"
        return res

class Othello(BaseGame):
    """
    Represents the othello game extension of the bot

    Attributes
    ----------
    bot : discord.ext.commands.Bot
        The bot that loaded this extension
    """

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__("othello")
        self.bot = bot
        self.description = "games : Othello"

    @josix_slash(description="Launch a game of Othello", give_xp=True)
    @option(
        input_type=discord.Member,
        name="opponent",
        description="Mention of your opponent",
        required=True
    )
    async def othello(self, ctx: ApplicationContext, opponent: discord.Member):
        if ctx.author.id == opponent.id:
            await ctx.respond("You can't challenge yourself")
            return

        if self.checkPlayers(ctx.author.id, opponent.id):
            await ctx.respond("One of the players is already in a game. If not, use `/quit_game` command")
            return

        idGame = self.initGame(ctx.author.id, opponent.id)
        first = randint(0, 1)
        view = OthelloView(ctx.interaction, self, idGame, ctx.author, opponent, first)
        embed = discord.Embed(
            title="Othello Game",
            description=f"{view.currentPlayer.mention}'s turn !",
            color=0x0089FF
        )
        embed.add_field(name="", value=view)
        await ctx.respond(embed=embed, view=view)

    @josix_slash(description="See othello's rules")
    async def othello_rules(self, ctx: ApplicationContext):
        embed = discord.Embed(
            title="Rules",
            description="Rules for the game othello",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.add_field(
            name="Rule 1",
            value="There is 2 players, white and black. The winner is the one with the most tokens on the board of his color at the end.",
            inline=False
        )
        embed.add_field(
            name="Rule 2",
            value="When it's your turn you must place your token near one of your opponent's tokens (diagonals not included) and at least flip one token.",
            inline=False
        )
        embed.add_field(
            name="Rule 3",
            value="You flip the opponent's tokens when they are between 1 of your tokens and the one you just placed (no recursion with the flipped ones)."
        )
        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Othello(bot))