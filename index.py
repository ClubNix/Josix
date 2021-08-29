# Importation modules

import discord
from discord.ext import commands
from discord.ext import tasks
import mysql.connector
from mysql.connector import errorcode

import cogs.admin as admin
import cogs.events as events
import cogs.usage as usage
import cogs.stats as stats
import cogs.games as games
import cogs.fun as fun

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

bot = commands.Bot(command_prefix = "s.", description = "Bot for useless statistics", intents = intents)
bot.remove_command("help")
        
try:
    cnx = mysql.connector.connect(user = USER,
                                  password = PASSWORD,
                                  host = HOST,
                                  database = DATABASE)

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with the username or/and password")

    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")

    elif err.errno == errorcode.CR_UNKNOWN_HOST:
        print("Unknown host")

    else:
        print(err)
else:
    print("Bot successfully connected to database")
    cursor = cnx.cursor()

    bot.add_cog(admin.Admin(bot, cursor, cnx))
    bot.add_cog(events.Events(bot, cursor, cnx))
    bot.add_cog(usage.Usage(bot, cursor))
    bot.add_cog(stats.Stats(bot, cursor))
    bot.add_cog(games.Games(bot))
    bot.add_cog(fun.Fun(bot))

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
async def unload(ctx, name=None):
    if name:
        bot.unload_extension(name)

##########
##########
##########

async def getEmbedStat(guild : discord.Guild, row = None) -> discord.Embed:
        selectM = f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongG WHERE idGuild = {guild.id}) FROM BelongG WHERE idGuild = {guild.id} ORDER BY numberMsg DESC LIMIT 5;"
        selectR = f"SELECT idReact, nameReact, numberReact, (SELECT SUM(numberReact) FROM Reaction WHERE idGuild = {guild.id}) FROM reaction WHERE idGuild = {guild.id} ORDER BY numberReact DESC LIMIT 5;"
        selectC = f"SELECT idChannel, numberMsg FROM Channel WHERE idGuild = {guild.id} ORDER BY numberMsg DESC LIMIT 5;"

        cursor.execute(selectM)
        topMember = ""
        for id, number, totalM in cursor.fetchall():
            user = bot.get_user(id)

            if user == None:
                delUser = f"DELETE FROM BelongG WHERE idUser = {id} AND idGuild = {guild.id};"
                cursor.execute(delUser)
            else:
                topMember += f"{user.mention} : **{number}**\n"

        cursor.execute(selectR)
        topReact = ""
        for id, name, number, totalR in cursor.fetchall():
            emoji = bot.get_emoji(id)

            if emoji == None:
                delEmoji = f"DELETE FROM Reaction WHERE idReact = {id};"
                cursor.execute(delEmoji)
            else:
                topReact += f"<:{name}:{id}> : **{number}**\n"

        cursor.execute(selectC)
        topChan = ""
        for id, number in cursor.fetchall():
            chan = bot.get_channel(id)

            if chan == None:
                delBC = f"DELETE FROM BelongC WHERE idChan = {id};"
                delChan = f"DELETE FROM Channel WHERE idChan = {id};"
                cursor.execute(delBC)
                cursor.execute(delChan)
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
        #count
        embed.add_field(name = "Total messages send", value = totalM)
        embed.add_field(name = "Total usage of the key word", value = resKW)
        embed.add_field(name = "Total reactions used", value = totalR)
        #top
        embed.add_field(name = "Top active members :", value = topMember)
        embed.add_field(name = "Top active channels :", value = topChan)
        embed.add_field(name = "Top used reactions :", value = topReact)
        return embed

##########
##########
##########

@tasks.loop(hours = 24)
async def sendStat():
    select = f"""SELECT idGuild, chanStatID, newMembers, lostMembers, totalMembers, lastSend, keyWord, nbKeyWord
                  FROM Guild
                  WHERE (sendStatus = '1' AND DATEDIFF(CAST(NOW() AS DATE), lastSend) >= 1)
                     OR (sendStatus = '2' AND DATEDIFF(CAST(NOW() AS DATE), lastSend) >= 7)
                     OR (sendStatus = '3' AND DATEDIFF(CAST(NOW() AS DATE), lastSend) >= 30);"""

    cursor.execute(select)
    query1 = cursor.fetchall()

    for row in query1:
        guild = bot.get_guild(row[0])
        chan = bot.get_channel(row[1])

        embed = await getEmbedStat(guild, row)
        await chan.send(embed = embed)

        upd_guild = f"UPDATE Guild SET newMembers = 0, lostMembers = 0, lastSend = CAST(NOW() AS DATE) WHERE idGuild = {row[0]};"
        upd_belongG = f"UPDATE BelongG SET numberMsg = 0 WHERE idGuild = {guild.id};"
        upd_chan = f"UPDATE Channel SET numberMsg = 0 WHERE idGuild = {guild.id};"
        upd_react = f"UPDATE Reaction SET numberReact = 0 WHERE idGuild = {guild.id};"

        cursor.execute(upd_guild)
        cursor.execute(upd_belongG)
        cursor.execute(upd_chan)
        cursor.execute(upd_react)

    cnx.commit()

##########
##########
##########

if __name__ == "__main__":
    main()
