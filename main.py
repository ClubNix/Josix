import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
import sys

import cogs

load_dotenv()
TOKEN = os.getenv("discord")

# Quelles informations notre bot va utiliser
intents = discord.Intents.none()
intents.members = True
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(command_prefix = "j!", #Le prefix des commandes
                   description = "Josix !", 
                   activity = discord.Game("stats and j!help"), # L'activité affichée (joue à ...) 
                   help_command = None, # Pour désactiver la commande help par défaut
                   intents = intents)

def main():
    global bot
    for name in cogs.FILES: #FILES dans __init__ donc accessible via l'import cogs
        bot.load_extension("cogs." + name)
        print("Extension " + name + " loaded")
    bot.run(TOKEN)

# L'event se lance quand le bot démarre (il ne faut mettre aucun appel à l'API dedans !)
@bot.event
async def on_ready():
    print("\n----- J'aime les Stats ----- \n")

@bot.command(hidden = True)
@commands.is_owner() # Regarde si l'auteur est l'owner du bot
async def stop(ctx):
    await ctx.send("Stop !")
    await bot.close()

@bot.command(hidden = True)
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Restart !")
    await bot.close()
    print("*******************\n" + 
          "----- Restart -----\n" + 
          "*******************\n")
    os.execv(sys.executable, ['python3'] + sys.argv)

if __name__ == "__main__":
    main()