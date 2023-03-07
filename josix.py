import discord
from discord.ext import commands
from discord import ExtensionNotFound, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed

from dotenv import load_dotenv
from cogs import FILES

import os
import logwrite as log

load_dotenv()
TOKEN = os.getenv("discord")

class Josix(commands.Bot):
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

if __name__ == "__main__":
    # The informations available for the bot
    intents = discord.Intents.none()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    intents.reactions = True

    josix = Josix(intents)
    josix.run(TOKEN)