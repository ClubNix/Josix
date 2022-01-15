import discord
from discord.ext import commands

import json
import os

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, 'data.json')
with open(file_path, 'r') as data:
    credentials = json.load(data)

TOKEN = credentials["token"]

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

def main(bot : commands.Bot):
    bot.run(TOKEN)

# L'event se lance quand le bot démarre (il ne faut mettre aucun appel à l'API dedans !)
@bot.event
async def on_ready():
    print("\n----- J'aime les Stats ----- \n")

@bot.command(hidden = True)
async def stop(ctx):
    await ctx.send("Stop !")
    await bot.close()

if __name__ == "__main__":
    main(bot)