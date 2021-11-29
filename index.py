##########
########## Importation modules
##########

import discord
from discord.ext import commands
from discord.ext import tasks

from database.database import DatabaseHandler

import os
import sys 
import json

######
###### Initialisation
######

"""
On choisit quelles informations le bot
va traiter. Tout ce qui n'est pas utile 
n'est pas ajouté pour réduire le traffic.
"""
intents = discord.Intents.none()
intents.members = True # Informations linked to the members
intents.guilds = True # Informations linked to the servers
intents.messages = True # Informations linked to the messages
intents.reactions = True # Informations linked to the reactions
intents.voice_states = True # Informations linked to the voice channel activity

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, 'data.json')
with open(file_path, 'r') as data:
    credentials = json.load(data)

TOKEN = credentials["token"]
USER = credentials["user"]
PASSWORD = credentials["password"]
HOST = credentials["host"]
DATABASE = credentials["database"]

# Connexion to the database with the DatabaseHandler file
DB = DatabaseHandler(USER,
                     PASSWORD,
                     HOST,
                     DATABASE)

# Creation of the bot (instance of commands.Bot)
bot = commands.Bot(command_prefix = "s.",
                   description = "Bot for useless statistics",
                   activity = discord.Game("stats and s.help"),
                   help_command = None,
                   intents = intents)

# Main function to launch the bot (and load the cogs / extensions)
def main():
    global bot
    for name in init.names:
        bot.load_extension("cogs." + name)
        print("Extension " + name + " loaded")
    bot.run(TOKEN)

@bot.event
async def on_ready():
    print("\n----- J'aime les Stats ----- \n")
    sendStat.start() # Start the loop (sendStat function)

##########
########## Administrative commands 
########## Only the owners can use it
##########

"""
Commands are hiddenn (hidden parameter) to make the
help command easier and not show them in the embed
"""

@bot.command(hidden = True)
@commands.is_owner()
async def leave(ctx):
    await ctx.send("I'm leaving because you're just a bunch of garbage")
    await bot.close()

@bot.command(hidden = True)
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Restarting myself, because I'm too cool !")
    await bot.close()
    os.execv(sys.executable, ['python3'] + sys.argv)

@bot.command(hidden = True)
@commands.guild_only()
@commands.is_owner()
async def dm(ctx, member : discord.User, *txt):
    await member.send(" ".join(txt))
    await ctx.message.add_reaction("✅")

@bot.command(hidden = True)
@commands.is_owner()
async def loadCog(ctx, name = None):
    if name:
        bot.load_extension("cogs." + name)

@bot.command(hidden = True)
@commands.is_owner()
async def unload(ctx, name = None):
    if name:
        bot.unload_extension("cogs." + name)

@bot.command(hidden = True)
@commands.is_owner()
async def reload(ctx, name = None):
    if name:
        try:
            bot.reload_extension("cogs." + name)
        except:
            bot.load_extension("cogs." + name)

##########
########## Main loop to realise the daily send of the stats
##########

async def getEmbedStat(guild : discord.Guild, row = None) -> discord.Embed:
        """
        A function to create the embed for the stats of each server
        The informations are extracted from the database with DatabaseHandler
        and used to create the embed and the stats
        """

        # Get the informations about the members, reactions and channels of the server
        queryM, queryR, queryC = DB.embedStat(guild)

        # Creating the leaderboard of the members 
        topMember = ""
        for id, number, totalM in queryM:
            user = bot.get_user(id)

            if user == None:
                DB.deleteBG(id, 0)
            else:
                topMember += f"{user.mention} : **{number}**\n"

        # Creating the leaderboard of the reactions
        topReact = ""
        for id, name, number, totalR in queryR:
            emoji = bot.get_emoji(id)

            if emoji == None:
                DB.deleteReact(id)
            else:
                topReact += f"<:{name}:{id}> : **{number}**\n"

        # Creating the leaderboard of the channels
        topChan = ""
        for id, number in queryC:
            chan = bot.get_channel(id)

            if chan == None:
                DB.deleteChan(id)
            else:
                topChan += f"<#{id}> : **{number}**\n"

        # Get the number of use of the key-words
        resKW = ""
        if row[6] == "":
            resKW = "No key-word"
        else:
            resKW = row[8]

        embed = discord.Embed(title = f"Statistics of the server {guild.name}", description = f"Last send : {row[5]}", color = 0x0089FF)
        embed.set_author(name = bot.user, icon_url = bot.user.avatar_url)
        embed.set_thumbnail(url = guild.icon_url)
        # Members
        embed.add_field(name = "Total members :", value = row[4])
        embed.add_field(name = "New members :", value = row[2])
        embed.add_field(name = "Lost members :", value = row[3])
        # Count
        embed.add_field(name = "Total messages send", value = totalM)
        embed.add_field(name = "Total usage of the key word", value = resKW)
        embed.add_field(name = "Total reactions used", value = totalR)
        # Top
        embed.add_field(name = "Top active members :", value = topMember)
        embed.add_field(name = "Top active channels :", value = topChan)
        embed.add_field(name = "Top used reactions :", value = topReact)
        return embed

@tasks.loop(hours = 24)
async def sendStat():
    """
    The loop (task) to send the stats
    Get all the registered servers that need to get their stats
    Get the embed and send it for each server, after that, reset the stats.
    """
    query1 = DB.getGuilds()

    for row in query1:
        guild = bot.get_guild(row[0])
        chan = bot.get_channel(row[1])
        embed = await getEmbedStat(guild, row)
        await chan.send(embed = embed)

        if row[8] == "1":
            DB.updStat(row[0])
    DB.commitQ() # Commit all the changes made in the for loop 

##########
##########
##########

if __name__ == "__main__":
    main()
