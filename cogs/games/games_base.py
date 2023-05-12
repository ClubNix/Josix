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

    def checkPlayers(self, idUser, idOpponent: int = None) -> bool:
        """Check if one of the two players are already in a game"""
        user = bool(self._db.getGameFromUser(idUser))
        oppo = bool(self._db.getGameFromUser(idOpponent)) if idOpponent else False
        return user or oppo

    def initGame(self, playerId: int, oppoId: int = None) -> None:
        self._db.addGameFromName(self.name, playerId, oppoId)

    def stopGame(self, idUser: int) -> None:
        self._db.quitGame(idUser)


class BaseView(View):
    def __init__(self, interaction: discord.Interaction, game: BaseGame, ogPlayer: Member, *args) -> None:
        super().__init__(timeout=15.0, disable_on_timeout=True, *args)
        self.interaction = interaction
        self.game = game
        self.ogPlayer = ogPlayer

    async def on_timeout(self) -> None:
        self.stopGame()
        await self.interaction.edit_original_response(content="Game stopped due to timeout", view=self)

    def stopGame(self) -> None:
        self.disable_all_items()
        self.stop()
        self.game.stopGame(self.ogPlayer.id)

def setup(bot: commands.Bot):
    bot.add_cog(Games(bot))