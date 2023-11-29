import discord
from discord.ext import commands

import logwrite as log

from dotenv import load_dotenv
from os import getenv
from database.database import DatabaseHandler
from psycopg2 import Error


EXIT = True


class Josix(commands.Bot):
    """
    The main class that represents Josix bot

    Attributes
    ----------
    db : DatabaseHandler
        A handler for the connection with the database to perform requests

    Methods
    -------
    run()
        Run the bot
    """
    load_dotenv(".env.dev")
    _TOKEN = getenv("DISCORD")

    def __init__(self, bot_intents: discord.Intents) -> None:
        super().__init__(
            description="Josix !",
            activity=discord.Game("/help and stats"), # The activity
            intents=bot_intents,
            help_command=None
        )
        try:
            self.db = DatabaseHandler()
        except Error as error:
                log.writeError(log.formatError(error))
                if EXIT:
                    exit(1)
        self._extensions()

    def _extensions(self) -> None:
        """
        Load all the extensions of the bot.

        Goes recursively in the cogs file and load every python
        file that does not starts with an underscore
        
        Once done, check the results for each extension, and log it
        """
        try:
            res = self.load_extension("cogs", recursive=True, store=True)
            for cogName, cogRes in res.items():
                if isinstance(cogRes, Exception):
                    log.writeError(log.formatError(cogRes))

                elif isinstance(cogRes, bool) and cogRes:
                    log.writeLog(f"Extension {cogName} succesfully loaded")
                
        except Exception as error:
            log.writeError(log.formatError(error))

    def run(self) -> None:
        super().run(Josix._TOKEN)


if __name__ == "__main__":
    # The informations available for the bot
    intents = discord.Intents.none()
    intents.members = True
    intents.guilds = True
    intents.guild_messages = True
    intents.bans = True
    intents.emojis_and_stickers = True
    intents.webhooks = True
    intents.messages = True
    intents.message_content = True
    intents.reactions = True
    intents.auto_moderation_configuration = True
    intents.auto_moderation_execution = True

    josix = Josix(intents)
    josix.run()
