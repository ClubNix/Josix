import discord
from discord.ui import View
from discord.ext import commands
from discord import ApplicationContext, Member

import datetime as dt

from josix import Josix
from bot_utils import JosixCog, josix_slash
from cogs.xp_system import XP
from database.database import DatabaseHandler
from database.services import discord_service, games_service

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
        games_service.delete_games(self.bot.get_handler())

    @josix_slash(description="Quit your current game")
    async def quit_game(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        games_service.quit_game(self.bot.get_handler(), ctx.author.id)
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
            games_service.add_game_type(self._db, self.name)

    def grantsXP(self, member: Member, guild: discord.Guild, amount: int):
        idMember = member.id
        userDB, guildDB, userGuildDB = discord_service.get_link_user_guild(self._db, idMember, guild.id)

        if not userDB:
            discord_service.add_user(self._db, idMember)
        if not guildDB:
            discord_service.add_guild(self._db, guild.id)
            guildDB = discord_service.get_guild(self._db, guild.id)
        if not userGuildDB:
            discord_service.add_user_in_guild(self._db, idMember, guild.id)
            userGuildDB = discord_service.get_user_in_guild(self._db, idMember, guild.id)

        if userGuildDB.isUserBlocked:
            return

        currentXP = userGuildDB.xp
        newXP, level = XP.checkUpdateXP(currentXP, amount)
        self._db.updateUserXP(idMember, guild.id, level, newXP, dt.datetime.now())


    def checkGame(self) -> bool:
        return bool(games_service.get_game_type(self._db, self.name))

    def checkGameState(self, idGame: int, idUser: int) -> bool:
        return bool(games_service.get_existing_game(self._db, idGame, idUser))

    def checkPlayers(self, idUser, idOpponent: int = None) -> bool:
        """Check if one of the two players are already in a game"""
        user = bool(games_service.get_game_from_user(self._db, idUser))
        oppo = bool(games_service.get_game_from_user(self._db, idOpponent)) if idOpponent else False
        return user or oppo

    def initGame(self, playerId: int, oppoId: int = None) -> int:
        testP1 = bool(discord_service.get_user(self._db, playerId))
        testP2 = bool(discord_service.get_user(self._db, oppoId)) if oppoId else True

        if not testP1:
            discord_service.add_user(self._db, playerId)
        if not testP2:
            discord_service.add_user(self._db, oppoId)
            
        res = games_service.add_game(self._db, self.name, playerId, oppoId)
        if res is None:
            raise Exception("The game could not be loaded")
        return res

    def stopGame(self, idGame: int) -> None:
        games_service.delete_single_game(self._db, idGame)


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