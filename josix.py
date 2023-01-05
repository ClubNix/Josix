import discord
from discord.ext import commands
from discord import ExtensionError

from dotenv import load_dotenv
from cogs import FILES

import os
import logwrite as log

load_dotenv()
TOKEN = os.getenv("discord")

"""
    TODO 
    - finish migration for all commands
    - repair user parameter for avatar and check for int parameter (createReactRole and clear in admin file)
    - repair parameter description broken (add_askip) called twice (first with description, then without)
"""

def main():
    # The informations available for the bot
    intents = discord.Intents.none()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    intents.reactions = True
    intents.voice_states = True

    bot = commands.Bot(description = "Josix !", 
                       activity = discord.Game("stats and j!help"), # The activity
                       intents = intents,
                       help_command=None
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