from discord import SlashCommand
from typing import Callable
from discord.commands.core import application_command
from discord.ext.commands import Cog

class JosixCog(Cog):
    """A class representing a Cog for Josix with a special attribute for the help command

    Attributes
    ----------
    showHelp : bool
        Wether or not this cog should be displayed in the help command
    isGame : bool
        Boolean to know if this cog is a game cog
    isOwner : bool
        Boolean to know if this cog is a owner cog
    """
    def __init__(self, showHelp: bool = True, isGame: bool = False, isOwner: bool = False) -> None:
        super().__init__()
        self.showHelp = showHelp
        self.isGame = isGame
        self.isOwner = isOwner

class JosixSlash(SlashCommand):
    """
    A subclass of SlashCommand that implements Josix's slash commands

    Created to have a better xp handling with a new attribute, give_xp

    Attributes
    ----------
    give_xp : bool
        boolean representing if the command grants xp when executed by an user
    """
    def __init__(self, func: Callable, *args, **kwargs) -> None:
        super().__init__(func, *args, **kwargs)

        self.give_xp: bool = kwargs.get("give_xp", False)
        if not isinstance(self.give_xp, bool): raise TypeError("give_xp must be a boolean")

def josix_slash(**kwargs):
    """Decorator for josix's slash commands that invokes application_comand.

    Returns
    -------
    Callable[..., JosixSlash]
        A decorator that converts the provided method into a JosixSlash.
    """
    return application_command(cls=JosixSlash, **kwargs)