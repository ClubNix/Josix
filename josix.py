import discord
from discord.ext import commands
from discord.ext.commands.errors import ExtensionError

from dotenv import load_dotenv
import psycopg2 
import os
import sys

from cogs import FILES

load_dotenv()
TOKEN = os.getenv("discord")

# The informations available for the bot
intents = discord.Intents.none()
intents.members = True
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.voice_states = True

try:
    cnx = psycopg2.connect(
        host="localhost",
        database=os.getenv("db_name"),
        user=os.getenv("db_user"),
        password=os.getenv("db_pwd")
    )

    print("\n------------------------------------------")
    print("Connection to database succesfully created")
    print("------------------------------------------\n")
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
    exit(1)

bot = commands.Bot(command_prefix = "j!", # The prefix
                   description = "Josix !", 
                   activity = discord.Game("stats and j!help"), # The activity
                   help_command = None, # Desactivating the default help command (to overwrite it)
                   intents = intents
)

def main():
    global bot
    
    for name in FILES: # FILES in the __init__.py file
        try:
            bot.load_extension("cogs." + name)
            print("Extension " + name + " loaded")
        except ExtensionError as error:
            print(error)
    bot.run(TOKEN)

# Event triggered when the bot is ready to use
@bot.event
async def on_ready():
    print("\n----- J'aime les Stats -----\n")

@bot.command(hidden = True)
@commands.is_owner() # Check if the author if the owner of the bot
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
          "*******************\n"
    )
    os.execv(sys.executable, ['python3'] + sys.argv)

if __name__ == "__main__":
    main()