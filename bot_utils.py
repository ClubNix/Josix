from discord import SlashCommand
from typing import Callable
from discord.commands.core import application_command

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
