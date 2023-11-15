import discord
from discord.ui import View
from discord.ext import commands
from discord import ApplicationContext, Member

import datetime as dt

from josix import Josix
from bot_utils import JosixCog, josix_slash
from cogs.xp_system import XP
from database.database import DatabaseHandler

class Games(JosixCog):
    """
    Represents the games functionalities extension of the bot

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    """

    def __init__(self, bot: Josix) -> None:
        super().__init__(isGame=True)
        self.bot = bot
        self.description = "games : Base"
        self._cleanGames()

    def _cleanGames(self):
        self.bot.db.deleteGames()

    @josix_slash(description="Quit your current game")
    async def quit_game(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        self.bot.db.quitGame(ctx.author.id)
        await ctx.respond("You just left your game")


# ------------
# Base Classes
# ------------

class BaseGame(JosixCog):
    """
    Base class for all the games.
    Used to be inherited by all the games to access common functionalities

    Attributes
    ----------
    name : str
        The name of the game
    """

    def __init__(self, gameName: str, db: DatabaseHandler) -> None:
        super().__init__(isGame=True)
        self.name = gameName
        self._db = db

        if not self.checkGame():
            self._db.addGameType(self.name)

    def grantsXP(self, member: Member, guild: discord.Guild, amount: int):
        idMember = member.id
        userDB, guildDB, userGuildDB = self._db.getUserGuildLink(idMember, guild.id)

        if not userDB:
            self._db.addUser(idMember)
        if not guildDB:
            self._db.addGuild(guild.id)
            guildDB = self._db.getGuild(guild.id)
        if not userGuildDB:
            self._db.addUserGuild(idMember, guild.id)
            userGuildDB = self._db.getUserInGuild(idMember, guild.id)

        if userGuildDB.isUserBlocked:
            return

        currentXP = userGuildDB.xp
        newXP, level = XP.checkUpdateXP(currentXP, amount)
        self._db.updateUserXP(idMember, guild.id, level, newXP, dt.datetime.now())


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
        if res is None:
            raise Exception("The game could not be loaded")
        return res

    def stopGame(self, idGame: int) -> None:
        self._db.deleteGame(idGame)


class BaseView(View):
    """
    Base class for all the views.
    Used to be inherited by all the views of each game to access common functionalities

    Attributes
    ----------
    interaction : Interaction
        The interaction that called the View
    game : BaseGame
        The game launched by the user
    ogPlayer : Member
        The user that started the game
    idGame : int
        The ID of the game in the database
    """

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