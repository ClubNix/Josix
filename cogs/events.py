import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Exemple d'events dans une extension
    # Ici event qui se trigger lors de la réception d'un message
    @commands.Cog.listener()
    async def on_message(self, message):
        # Mention du bot présente dans le message envoyé
        if self.bot.mention in message.content:
            # Envoie un message dans le salon du message reçu
            message.channel.send(":angry:")


def setup(bot):
    bot.add_cog(Events(bot))