import discord
from discord.ext import commands
from discord import ExtensionError

from dotenv import load_dotenv
from cogs import FILES

import os
import logwrite as log

load_dotenv()
TOKEN = os.getenv("discord")

def main():
    # The informations available for the bot
    intents = discord.Intents.none()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    intents.reactions = True
    intents.voice_states = True

    bot = commands.Bot(command_prefix = "j!", # The prefix
                    description = "Josix !", 
                    activity = discord.Game("stats and j!help"), # The activity
                    help_command = None, # Desactivating the default help command (to overwrite it)
                    intents = intents
    )

    for name in FILES: # FILES in the __init__.py file
        try:
            bot.load_extension("cogs." + name)
            log.writeLog("Extension " + name + " Successfully loaded")
        except (ModuleNotFoundError, ExtensionError) as error:
            log.writeError(log.formatError(error))
    bot.run(TOKEN)

if __name__ == "__main__":
    main()