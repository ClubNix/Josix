import discord
from discord.ext import commands

from dotenv import load_dotenv
from os import getenv

import logwrite as log


class Josix(commands.Bot):
    """
    The main class that represents Josix bot

    Attributes
    ----------
    bot_intents : discord.Intents
        The intents that the bot will use

    Methods
    -------
    run()
        Run the bot
    """
    load_dotenv()
    _TOKEN = getenv("discord")

    def __init__(self, bot_intents: discord.Intents) -> None:
        super().__init__(
            description="Josix !",
            activity=discord.Game("/help and stats"), # The activity
            intents=bot_intents,
            help_command=None
        )
        self._extensions()

    def _extensions(self) -> None:
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
