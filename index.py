# Importation modules

import discord
from discord.ext import commands
from discord.ext import tasks

import cogs.admin as admin
import cogs.events as events
import cogs.usage as usage
import cogs.stats as stats
import cogs.games as games
import cogs.fun as fun
import cogs.__init__ as init 
from database.database import DatabaseHandler

import os
import sys 
import json

# Initialisation

intents = discord.Intents.default()  
intents.members = True
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.voice_states = True

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, 'data.json')
with open(file_path, 'r') as data:
    credentials = json.load(data)

TOKEN = credentials["token"]
USER = credentials["user"]
PASSWORD = credentials["password"]
HOST = credentials["host"]
DATABASE = credentials["database"]

DB = DatabaseHandler(USER,
                     PASSWORD,
                     HOST,
                     DATABASE)

bot = commands.Bot(command_prefix = "s.", description = "Bot for useless statistics", intents = intents)
bot.remove_command("help")

for name in init.names:
    bot.load_extension("cogs." + name)
    print("Extension " + name + " loaded")

"""
bot.add_cog(admin.Admin(bot))
bot.add_cog(events.Events(bot))
bot.add_cog(usage.Usage(bot))
bot.add_cog(stats.Stats(bot))
bot.add_cog(games.Games(bot))
bot.add_cog(fun.Fun(bot))"""

def main():
    global bot
    bot.run(TOKEN)


@bot.event
async def on_ready():
    print("J'aime les Stats")
    await bot.change_presence(activity = discord.Game(f"stats and {bot.command_prefix}help"))
    sendStat.start()

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
async def load(ctx, name = None):
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
##########
##########

async def getEmbedStat(guild : discord.Guild, row = None) -> discord.Embed:
        queryM, queryR, queryC = DB.embedStat(guild)

        topMember = ""
        for id, number, totalM in queryM:
            user = bot.get_user(id)

            if user == None:
                DB.deleteBG(id, 0)
            else:
                topMember += f"{user.mention} : **{number}**\n"

        topReact = ""
        for id, name, number, totalR in queryR:
            emoji = bot.get_emoji(id)

            if emoji == None:
                DB.deleteReact(id)
            else:
                topReact += f"<:{name}:{id}> : **{number}**\n"

        topChan = ""
        for id, number in queryC:
            chan = bot.get_channel(id)

            if chan == None:
                DB.deleteChan(id)
            else:
                topChan += f"<#{id}> : **{number}**\n"

        resKW = ""
        if row[6] == "":
            resKW = "No key-word"
        else:
            resKW = row[7]

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

##########
##########
##########

@tasks.loop(hours = 24)
async def sendStat():
    query1 = DB.getGuilds()

    for row in query1:
        guild = bot.get_guild(row[0])
        chan = bot.get_channel(row[1])
        embed = await getEmbedStat(guild, row)
        await chan.send(embed = embed)

        DB.updStat(row[0])
    DB.commitQ()

##########
##########
##########

if __name__ == "__main__":
    main()
