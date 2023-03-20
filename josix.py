import discord
from discord.ext import commands
from discord import ExtensionNotFound, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed

from dotenv import load_dotenv
from os import getenv
from cogs import FILES

import logwrite as log


class Josix(commands.Bot):
    load_dotenv()
    _TOKEN = getenv("discord")

    def __init__(self, intents: discord.Intents):
        super().__init__(
            description = "Josix !", 
            activity = discord.Game("/help and stats"), # The activity
            intents = intents,
            help_command=None
        )
        self._extensions()

    def _extensions(self):
        for name in FILES: # FILES in the __init__.py file
            try:
                self.load_extension("cogs." + name)
                log.writeLog("Extension " + name + " Successfully loaded")
            except (ModuleNotFoundError, ExtensionNotFound, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed) as error:
                log.writeError(log.formatError(error))

    def run(self):
        super().run(Josix._TOKEN)

if __name__ == "__main__":
    # The informations available for the bot
    intents = discord.Intents.none()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    intents.reactions = True

    josix = Josix(intents)
    josix.run()