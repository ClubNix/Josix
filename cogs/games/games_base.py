import discord
from discord.ui import View
from discord.ext import commands
from discord import ApplicationContext, Member

from database.database import DatabaseHandler

import os

class Games(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "games : Base"
        self.db = DatabaseHandler(os.path.basename(__file__))
        self._cleanGames()

    def _cleanGames(self):
        self.db.deleteGames()

    @commands.slash_command(description="Quit your current game")
    async def quit_game(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        self.db.quitGame(ctx.author.id)
        await ctx.respond("You just left your game")


# ------------
# Base Classes
# ------------

class BaseGame(commands.Cog):
    def __init__(self, gameName: str) -> None:
        self.name = gameName
        self._db = DatabaseHandler(self.name)

        if not self.checkGame():
            self._db.addGameType(self.name)

    def checkGame(self) -> bool:
        return bool(self._db.getGameType(self.name))

    def checkGameState(self, idGame: int, idUser: int) -> bool:
        return bool(self._db.getExistingGame(idGame, idUser))

    def checkPlayers(self, idUser, idOpponent: int = None) -> bool:
        """Check if one of the two players are already in a game"""
        user = bool(self._db.getGameFromUser(idUser))
        oppo = bool(self._db.getGameFromUser(idOpponent)) if idOpponent else False
        return user or oppo

    def initGame(self, playerId: int, oppoId: int = None) -> int:
        testP1 = bool(self._db.getUser(playerId))
        testP2 = bool(self._db.getUser(oppoId)) if oppoId else True

        if not testP1:
            self._db.addUser(playerId)
        if not testP2:
            self._db.addUser(oppoId)
            
        res = self._db.addGameFromName(self.name, playerId, oppoId)
        return res[0]

    def stopGame(self, idGame: int) -> None:
        self._db.deleteGame(idGame)


class BaseView(View):
    def __init__(self, interaction: discord.Interaction, game: BaseGame, idGame: int, ogPlayer: Member, *args) -> None:
        super().__init__(timeout=180.0, disable_on_timeout=True, *args)
        self.interaction = interaction
        self.game = game
        self.ogPlayer = ogPlayer
        self.idGame = idGame

    async def checkGameState(self) -> bool:
        res = self.game.checkGameState(self.idGame, self.ogPlayer.id)
        if not res:
            self.stopGame()
            await self.interaction.edit_original_response(content="A user stopped this game", view=self)
        return res

    async def on_timeout(self) -> None:
        self.stopGame()
        await self.interaction.edit_original_response(content="Game stopped due to timeout", view=self)

    def stopGame(self) -> None:
        self.disable_all_items()
        self.stop()
        self.game.stopGame(self.idGame)

def setup(bot: commands.Bot):
    bot.add_cog(Games(bot))