# Importation modules

import discord
from discord.ext import commands
from discord.ext import tasks
import matplotlib
import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import errorcode

import random
import datetime as dt
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

with open("C:/Users/Erwann/OneDrive/Documents/Code/bot/StatBot/data.json") as data:
    credentials = json.load(data)

TOKEN = credentials["token"]
USER = credentials["user"]
PASSWORD = credentials["password"]
HOST = credentials["host"]
DATABASE = credentials["database"]

bot = commands.Bot(command_prefix = "s.", description = "Bot for useless statistics", intents = intents)
bot.remove_command("help")

#mysql -h localhost -u root -p
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


# Evenements

@bot.event
async def on_ready():
    print("J'aime les Stats")
    await bot.change_presence(activity = discord.Game(f"stats and {bot.command_prefix}help"))
    sendStat.start()

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author != bot.user:
        if not message.guild: 
            chan = bot.get_channel(737049189208555591)
            await chan.send(f"**{message.author.name}** : {message.content}")

    if not message.author.bot and message.guild:
        idAuth = message.author.id
        idChan = message.channel.id
        idGuild = message.guild.id

        getKW = f"SELECT keyWord FROM Guild WHERE idGuild = {idGuild};"
        cursor.execute(getKW)
        queryG = cursor.fetchall()

        if len(queryG) == 0:
            members = message.guild.members
            count = 0
            for member in members:
                if not member.bot:
                    count += 1

            add_user = f"INSERT IGNORE User VALUES({member.id}, {member.created_at.year})"
            cursor.execute(add_user)

            add_guild = "INSERT INTO Guild(idGuild, totalMembers) VALUES(%s, %s);"
            data_guild = (idGuild, count)
            cursor.execute(add_guild, data_guild)

        elif queryG[0][0] != "":
            if queryG[0][0] in message.content.lower():
                upd_kw = f"UPDATE Guild SET nbKeyWord = nbKeyWord + 1 WHERE idGuild = {idGuild};"
                cursor.execute(upd_kw)

        upd_chan = f"UPDATE Channel SET numberMsg = numberMsg + 1 WHERE idChannel = {idChan};"
    
        select1 = f"SELECT idUser FROM User WHERE idUser = {idAuth};"
        cursor.execute(select1)
        query1 = cursor.fetchall()

        select2 = f"SELECT idUser FROM BelongC WHERE idUser = {idAuth} AND idChannel = {idChan};"
        cursor.execute(select2)
        query2 = cursor.fetchall()

        select3 = f"SELECT idUser FROM BelongG WHERE idUser = {idAuth} AND idGuild = {idGuild};"
        cursor.execute(select3)
        query3 = cursor.fetchall()
        
        if len(query1) == 0:
            add_member = "INSERT INTO User VALUES(%s, %s, NULL);"
            data_member = (idAuth, message.author.created_at.year)
            upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {message.guild.id};"

            cursor.execute(add_member, data_member)
            cursor.execute(upd_guild)

        if len(query2) == 0:
            cursor.execute("INSERT IGNORE Channel(idChannel, idGuild) VALUES(%s, %s);", (message.channel.id, message.guild.id))
            add_belongC = "INSERT INTO BelongC VALUES(%s, %s, 0);"
            data_belongC = (idAuth, idChan)
            cursor.execute(add_belongC, data_belongC)

        if len(query3) == 0:
            add_belongG = "INSERT INTO BelongG VALUES(%s, %s, 0, 0);"
            data_belongG = (idAuth, idGuild)
            cursor.execute(add_belongG, data_belongG)
        
        upd_belongC = f"UPDATE BelongC SET numberMsg = numberMsg + 1 WHERE idChannel = {idChan} AND idUser = {idAuth};"
        upd_belongG = f"UPDATE BelongG SET numberMsg = numberMsg + 1 WHERE idGuild = {message.guild.id} AND idUser = {idAuth};"

        cursor.execute(upd_chan)
        cursor.execute(upd_belongC)
        cursor.execute(upd_belongG)
        cnx.commit()


@bot.event
async def on_guild_join(guild):
    await loadG(guild)

@bot.event
async def on_guild_remove(guild):
    del_belong = f"DELETE FROM BelongG WHERE idGuild = {guild.id};"
    del_chan = f"DELETE FROM Channel WHERE idGuild = {guild.id};"
    del_guild = f"DELETE FROM Guild WHERE idGuild = {guild.id};"

    cursor.execute(del_belong)
    cursor.execute(del_chan)
    cursor.execute(del_guild)
    cnx.commit()


@bot.event
async def on_member_join(member):
    if (member.bot):
        return
        
    update_join = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {member.guild.id};"
    cursor.execute(update_join)

    select = f"SELECT idUser FROM User WHERE idUser = {member.id};"
    cursor.execute(select)
    query = cursor.fetchall()

    if len(query) == 0:
        add_member = "INSERT INTO User VALUES(%s, %s, NULL);"
        data_member = (member.id, member.created_at.year)
        upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {member.guild.id};"

        cursor.execute(add_member, data_member)
        cursor.execute(upd_guild)

    add_belong = "INSERT INTO BelongG VALUES(%s, %s, 0, 0);"
    data_belong = (member.id, member.guild.id)
    cursor.execute(add_belong, data_belong)

    cnx.commit()


@bot.event
async def on_member_remove(member):
    if (member.bot):
        return

    update_rmv = f"UPDATE Guild SET lostMembers = lostMembers + 1, totalMembers = totalMembers - 1 WHERE idGuild = {member.guild.id};"
    cursor.execute(update_rmv)

    rmv_member = f"DELETE FROM BelongG WHERE idGuild = {member.guild.id} AND idUser = {member.id};"
    cursor.execute(rmv_member)
    cnx.commit()

@bot.event
async def on_guild_channel_create(channel):
    select = f"SELECT autoAdd FROM Guild WHERE idGuild = {channel.guild.id};"
    cursor.execute(select)
    query = cursor.fetchall()

    if query[0][0] == "1":
        add_channel = "INSERT INTO Channel VALUES(%s, %s, 0);"
        data_chan = (channel.id, channel.guild.id)
        cursor.execute(add_channel, data_chan)
        cnx.commit()

@bot.event
async def on_guild_channel_delete(channel):
    del_belong = f"DELETE FROM BelongC WHERE idChannel = {channel.id};"
    del_channel = f"DELETE FROM Channel WHERE idChannel = {channel.id};"

    cursor.execute(del_belong)
    cursor.execute(del_channel)
    cnx.commit()

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id == None or payload.member.bot:
        return

    guild = bot.get_guild(payload.guild_id)
    if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji():
        return

    select = f"SELECT idReact FROM Reaction WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
    cursor.execute(select)
    query = cursor.fetchall()

    if len(query) == 0:
        return

    upd_react = f"UPDATE Reaction SET numberReact = numberReact + 1 WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
    cursor.execute(upd_react)

    cnx.commit()

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id == None:
        return
    
    guild = bot.get_guild(payload.guild_id)
    if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji():
        return

    select = f"SELECT idReact FROM Reaction WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
    cursor.execute(select)
    query = cursor.fetchall()

    if len(query) == 0:
        return

    upd_react = f"UPDATE Reaction SET numberReact = numberReact - 1 WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
    cursor.execute(upd_react)

    cnx.commit()

@bot.event
async def on_reaction_clear(message, reactions):
    guild = bot.get_guild(message.guild.id)
    if len(guild.emojis) == 0:
        return

    for reaction in reactions:
        if not reaction.custom_emoji:
            return

        select = f"SELECT idReact FROM Reaction WHERE idGuild = {guild.id} AND idReact = {reaction.emoji.id};"
        cursor.execute(select)
        query = cursor.fetchall()

        if len(query) == 0:
            return

        upd_react = f"UPDATE Reaction SET numberReact = numberReact - {reaction.count} WHERE idGuild = {guild.id} AND idReact = {reaction.emoji.id};"
        cursor.execute(upd_react)

    cnx.commit()

@bot.event
async def on_guild_emojis_update(guild, before, after):
    select = f"SELECT idReact, nameReact FROM Reaction WHERE idGuild = {guild.id};"
    cursor.execute(select)
    query = cursor.fetchall()

    if len(before) < len(after):
        newEmoji = after[len(after) - 1]
        add_react = "INSERT INTO Reaction VALUES(%s, %s, %s, %s)"
        data_react = (newEmoji.id, guild.id, 0, newEmoji.name)
        cursor.execute(add_react, data_react)
        cnx.commit()
        return

    elif len(before) > len(after):
        for row in query:
            isPresent = False
            for emoji in after:
                if row[0] == emoji.id:
                    isPresent = True
                    break

            if not isPresent:
                del_react = f"DELETE FROM Reaction WHERE idReact = {row[0]};"
                cursor.execute(del_react)
                cnx.commit()
                return

    else:
        for emoji in after:
            for row in query:
                if row[0] == emoji.id:
                    if emoji.name != row[1]:
                        upd_react = f"UPDATE Reaction SET nameReact = '{emoji.name}' WHERE idReact = {emoji.id};"
                        cursor.execute(upd_react)
                        cnx.commit()
                        return

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    if before.channel == None:
        select = f"SELECT idUser FROM User WHERE idUser = {member.id};"
        cursor.execute(select)

        if len(cursor.fetchall()) == 0:
            add_user = "INSERT INTO User(idUser, yearDate) VALUES(%s, %s);"
            data_user = (member.id, member.created_at.year)
            add_belong = "INSERT INTO BelongG(idUser, idGuild) VALUES(%s, %s);"
            data_belong = (member.id, member.guild.id)
            upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {member.guild.id};"

            cursor.execute(add_user, data_user)
            cursor.execute(add_belong, data_belong)
            cursor.execute(upd_guild)

        upd_user = f"UPDATE User SET joinVoc = NOW() WHERE idUser = {member.id};"
        cursor.execute(upd_user)

    elif after.channel == None:
        select = f"SELECT joinVoc FROM User WHERE idUser = {member.id};"
        cursor.execute(select)
        dateJoin = cursor.fetchall()[0][0]
        delta = (dt.datetime.now() - dateJoin).total_seconds()

        upd_user = f"UPDATE User SET joinVoc = NULL WHERE idUser = {member.id};"
        upd_belong = f"UPDATE BelongG SET nbSecond = nbSecond + {delta} WHERE idUser = {member.id} AND idGuild = {before.channel.guild.id};"
        cursor.execute(upd_user)
        cursor.execute(upd_belong)
    
    cnx.commit()


# Fonctions

async def loadG(guild):
    select = f"SELECT idGuild FROM Guild WHERE idGuild = {guild.id};"
    cursor.execute(select)

    if len(cursor.fetchall()) > 0:
        return False

    members = guild.members
    count = 0
    for member in members:
        if not member.bot:
            count += 1

            add_user = f"INSERT IGNORE User VALUES({member.id}, {member.created_at.year})"
            cursor.execute(add_user)

    add_guild = "INSERT INTO Guild(idGuild, totalMembers) VALUES(%s, %s);"
    data_guild = (guild.id, count)
    cursor.execute(add_guild, data_guild)

    for chan in guild.text_channels:
        add_chan = "INSERT INTO Channel VALUES(%s, %s, %s);"
        data_chan = (chan.id, guild.id, 0)
        cursor.execute(add_chan, data_chan)

    for emoji in guild.emojis:
        add_emoji = "INSERT INTO Reaction VALUES(%s, %s, %s, %s);"
        data_emoji = (emoji.id, guild.id, 0, emoji.name)
        cursor.execute(add_emoji, data_emoji)

    cnx.commit()
    print(f"Added the guild {guild.name} to the database with \n• {count} members \n• {len(guild.text_channels)} text channels \n• {len(guild.emojis)} emojis")

    return True

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

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Sorry, you don't have the required permissions")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("This command requires one or several arguments")

    elif isinstance(error, discord.Forbidden):
        await ctx.send("I can't send the message, if it's for the nude, it's private so let me talk to you !")

    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("This command doesn't exist")

    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send("You still on a cooldown for this command, please wait")

    elif isinstance(error, commands.DisabledCommand):
        await ctx.send("This command is disabled")

    else:
        print(error)
        await ctx.send("An error occured, it's because my dumb owner doesn't know how to code. \nSorry to bother you but could you report it to him ?")


# Commandes

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

@bot.command(description = "Help command of the bot", aliases = ["HELP"])
async def help(ctx, commandName = None):
    if commandName == None:
        lst = ""
        for command in bot.commands:
            if not command.hidden:
                lst += f"`{command.name}`, "

        embed = discord.Embed(title = "Help command", description = f"Description of the commands, use `{bot.command_prefix}help [commandName]` to get more info about a specific command", color = 0x0089FF)
        embed.set_thumbnail(url = bot.user.avatar_url)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.add_field(name = "All commands :", value = lst[:len(lst) - 2], inline = False)
        embed.add_field(name = "Other informations :", value = f"""• Owner : {bot.get_user(237657579692621824)} \n• prefix : `{bot.command_prefix}`\n• Invite the bot : `{bot.command_prefix}invite` \n• More informations : `{bot.command_prefix}info`""")
        await ctx.send(embed = embed)

    else:
        cmd = bot.get_command(commandName)
        if cmd == None or cmd.hidden:
            await ctx.send("Unknown command :x:")
            return

        if len(cmd.aliases) == 0:
            al = "No aliases"
        else:
            al = ", ".join(cmd.aliases)

        if cmd.description == "":
            desc = "No description"
        else:
            desc = cmd.description

        usage = f"{bot.command_prefix}{cmd.name} "
        param = cmd.clean_params
        for val in param.values():
            default = val.default
            if str(default) != "<class 'inspect._empty'>":
                if default == None:
                    default = ""
                else:
                    default = f" = {default}"
                usage += f"[{val.name}{default}] "

            else:
                usage += f"<{val.name}> "

        embed2 = discord.Embed(title = "Help command", description = f"Description of the command **{cmd.name}**\n <> -> Forced parameters | [] -> Optional parameters", color = 0x0089FF)
        embed2.set_thumbnail(url = bot.user.avatar_url)
        embed2.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed2.add_field(name = "Aliases :", value = al)
        embed2.add_field(name = "Description :", value = desc, inline = False)
        embed2.add_field(name = "Usage :", value = usage)
        await ctx.send(embed = embed2)

@bot.command(description = "Important informations about the bot", aliases = ["INFO", "informations", "INFORMATIONS"])
async def info(ctx):
    embed = discord.Embed(title = "Important informations", description = "Read this to be aware of how I work", color = 0x0089FF)
    embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
    embed.set_thumbnail(url = bot.user.avatar_url)
    embed.add_field(name = "What I do ?",
                    value = "I register data about the members of the server and the server itself to show you some statistics. You can also use me for some fun commands and games of luck !",
                    inline = False)
    embed.add_field(name = "Channel activity",
                    value = "Be careful, I monitor when you create a channel and I add it to my database (see the `autoAdd` command) but if I can't read the messages I will not be able to update my data in this channel !",
                    inline = False)
    embed.add_field(name = "Kick, ban etc...",
                    value = "If a member is kicked or banned from the server I will instantly remove all his data from my database so be aware of that. Same thing if I leave the server, I will clean this part of my memory !",
                    inline = False)
    embed.add_field(name = "Disconnections",
                    value = "I can disconnect sometimes, remember to run the `load` commands to be sure that the server data is up-to-date !",
                    inline = False)
    embed.add_field(name = "Help me 😭 :",
                    value = "English is not the native language of my creator, if you find some errors in the sentences etc... report them ! \nSame thing if you find errors in the commands or get some ideas, it helps a lot !",
                    inline = False)
    await ctx.send(embed = embed)

@bot.command(description = "Get the link to invite the bot", aliases = ["INVITE", "link", "LINK"])
async def invite(ctx):
    await ctx.send("There's no link currently ¯\_(ツ)_/¯")

@bot.command(description = "To get the bio of my creator", aliases = ["BIO"])
async def bio(ctx):
    await ctx.send("https://dsc.bio/hitsuji")

@bot.command(description = "If you want to know how slow I am and get an insult, use it !", aliases = ["PING"])
async def ping(ctx):
    await ctx.send(f">Stupid ! You really think I am your slave {ctx.message.author.name} ?\n Btw I have a latency of {round(bot.latency*1000, 1)} ms") 

@bot.command(description = "I repeat your sentence", aliases = ["SAY"])
async def say(ctx, *txt):
    await ctx.send(" ".join(txt))
    await ctx.message.delete()

@bot.command(description = "Send a random custom emote of the server", aliases = ["EMOTE", "emoji", "EMOJI"])
@commands.guild_only()
async def emote(ctx):
    lst = ctx.guild.emojis

    if len(lst) == 0:
        await ctx.send("Sorry, but it seems that your guild doesn't have any custom emotes")
    else:
        await ctx.send(random.choice(lst))

@bot.command(description = "Everything is stonks", aliases = ["STONKS"])
async def stonks(ctx):
    await ctx.send("https://cdn.radiofrance.fr/s3/cruiser-production/2021/04/b4f7bf1d-42da-44c2-b912-2b038635e102/801x410_main-qimg-14aa45f4a944de6acb372fa0d4e61a7a.jpg")
    await ctx.send(f"Stonks {ctx.author.mention} !")
    await ctx.message.delete()

@bot.command(description = "I give you a nude in private", aliases = ["sendnude", "nude"])
async def sendNude(ctx):
    await ctx.author.send("https://media0.giphy.com/media/PpNTwxZyJUFby/giphy.gif?cid=ecf05e4786byc2ho9urw2i4yf3rztiahjv31h0yx5z4qrklc&rid=giphy.gif&ct=g")
    await ctx.message.add_reaction("👀")

@bot.command(description = "Use it to get your or someone avatar", aliases = ["AVATAR", "icon", "ICON"])
async def avatar(ctx, user : discord.User = None):
    if user == None:
        await ctx.send(ctx.message.author.avatar_url)
    else:
        await ctx.send(user.avatar_url)

@bot.command(description = "Some informations about me", aliases = ["ME", "bot", "BOT", "bot_info"])
async def me(ctx):
    me = bot.get_user(237657579692621824)

    selectG = "SELECT COUNT(idGuild) FROM Guild;"
    selectU = "SELECT COUNT(idUser) FROM User;"

    cursor.execute(selectG)
    queryG = cursor.fetchall()

    cursor.execute(selectU)
    queryU = cursor.fetchall()

    embed = discord.Embed(title = "Random data command", description = "Just some useless data", color = 0x0089FF)
    embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
    embed.add_field(name = "Creation date", value = bot.user.created_at.strftime("%D"))
    embed.add_field(name = "Developed with", value = f"Discord.py version {discord.__version__}")
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = "My creator", value = me)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = "Total of users", value = queryU[0][0])
    embed.add_field(name = "Number of servers", value = queryG[0][0])
    embed.add_field(name = "Number of commands", value = len(bot.commands))
    embed.set_footer(text = "I hope you have fun with my (useless) bot ^^")

    await ctx.send(embed = embed)



@bot.command(description = "Let's get a look at your luck and throw some dices", aliases = ["ROLL"])
async def roll(ctx, numberRolls : int = 1, mini : int = 1, maxi : int = 6):
    if mini < 0:
        mini = 1
    if maxi > 100:
        maxi = 6
    if mini > maxi:
        mini, maxi = 1, 6

    if numberRolls < 1 or numberRolls > 25:
        numberRolls = 1

    listeRoll = []
    for i in range(0, numberRolls):
        listeRoll.append(random.randint(mini,maxi))
    total = sum(listeRoll)
    moyenne = total / len(listeRoll)

    embed = discord.Embed(title = f"{ctx.message.author.name}'s rolls :game_die:", color = 0x008000)
    embed.set_author(name = ctx.message.author, icon_url = ctx.message.author.avatar_url)
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/709732615980056606/858436523531567104/combien-de-joueurs-a-la-pC3A9tanque-pC3A9tanque-gC3A9nC3A9ration.png")
    embed.add_field(name = "Number of rolls :", value = f"**{numberRolls}**", inline = False)
    embed.add_field(name = "Rolls obtained :", value = f"{listeRoll}", inline = False)
    embed.add_field(name = "Sum", value = f"{total}", inline = True)
    embed.add_field(name = "Average", value = f"{moyenne}", inline = True)
    await ctx.send(embed = embed)

@bot.command(description = "Heads or Tails ?", aliases = ["FLIP"])
async def flip(ctx):
    await ctx.send(f'> {random.choice(["Heads", "Tails"])}')

@bot.command(description = "Draw a card", aliases = ["CARD", "draw", "DRAW"])
async def card(ctx):
    cards = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J" , "Q", "K")
    colors = ("D", "S", "C", "H")
    card, color = random.choice(cards), random.choice(colors)
    file = discord.File(f"C:/Users/Erwann/OneDrive/Documents/Code/bot/StatBot/deck/{card}{color}.png", filename = "card.png")

    embed = discord.Embed(title = "Your card", description = "Here's the card you drew", color = 0x008000)
    embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/709732615980056606/872917800551845918/cards.png")
    embed.set_footer(text = "Images from https://github.com/danwei002/Cards-Bot")
    embed.set_image(url = f"attachment://card.png")
    await ctx.send(file = file, embed = embed)

@bot.command(description = "Play a game of roulette like you're at the casino !")
async def roulette(ctx):
    colors = ["🟩", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "⬛", "🟥",
              "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛",
              "🟥", "⬛", "🟥", "⬛", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥"
    ]
    column = ""
    dozen = ""
    color = ""

    number = random.randint(0, 36)
    color = colors[number]
    if number == 0:
        column = "No column"
    elif number % 3 == 1:
        column = "First column"
    elif number % 3 == 2:
        column = "Second column"
    else:
        column = "Third column"

    if number == 0:
        dozen = "No dozen"
    elif number < 13:
        dozen = "First dozen"
    elif number < 25:
        dozen = "Second dozen"
    else:
        dozen = "Third dozen"

    embed = discord.Embed(title = "Roulette time !", description = "Take your bet", color = 0x008000)
    embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/709732615980056606/874040662587232267/220px-Roulette-finlandsfarja.png")
    embed.add_field(name = "Number :", value = number)
    embed.add_field(name = "Color :", value = color, inline = True)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = "Column :", value = column, inline = True)
    embed.add_field(name = "Dozen :", value = dozen, inline = True)
    await ctx.send(embed = embed)

@bot.command(description = "See the amount of discord account created each year in your server", aliases = ["dateaccounts", "dates_accounts"])
@commands.guild_only()
async def dateAccounts(ctx):
    dates = {}
    year = int(dt.datetime.now().strftime("%Y"))
                
    for i in range(2015, year + 1):
        dates[i] = 0
        select = f"SELECT COUNT(yearDate) FROM BelongG bg INNER JOIN User u ON bg.idUser = u.idUser WHERE yearDate = {i} AND bg.idGuild = {ctx.guild.id};"
        cursor.execute(select)
        query = cursor.fetchall()
        if len(query) != 0:
            dates[i] += query[0][0]

    plt.bar(dates.keys(), dates.values())
    plt.xlabel("Année de création du compte")
    plt.ylabel("Nombre de comptes créés pour l'année")
    plt.savefig(f"./statDate_{ctx.guild.id}.png")
    plt.close()

    img = discord.File(f"./statDate_{ctx.guild.id}.png")
    await ctx.send(file = img)

    os.remove(f"./statDate_{ctx.guild.id}.png")

@bot.command(aliases = ["guildInfo", "server_info"], description = "Your server data")
@commands.guild_only()
async def serverInfo(ctx):
    server = ctx.guild

    select = f"SELECT COUNT(idUser) FROM BelongG WHERE idGuild = {server.id};"
    cursor.execute(select)

    embed = discord.Embed(title = "Guild's infos", description = "Your guild informations !", color = 0x0089FF)
    embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
    embed.set_thumbnail(url = server.icon_url)
    embed.add_field(name = "Name :", value = server.name, inline = True)
    embed.add_field(name = "Owner :", value = server.owner, inline = True)
    embed.add_field(name = "Region :", value = server.region, inline = True)
    embed.add_field(name = "Total users :", value = len(server.members), inline = True)
    embed.add_field(name = "Total registered users :", value = cursor.fetchall()[0][0], inline = True)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = "Total of text channels :", value = len(server.text_channels), inline = True)
    embed.add_field(name = "Total of voice channels :", value = len(server.voice_channels), inline = True)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = "Total of emojis :", value = len(server.emojis), inline = True)
    embed.add_field(name = "Total of roles :", value = len(server.roles), inline = True)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)

    await ctx.send(embed = embed)

@bot.command(description = "Set the frequency you want to receive your server stats", aliases = ["set", "SET", "setstats"])
@commands.guild_only()
@commands.has_permissions(manage_channels = True)
async def setStats(ctx, frequency = "daily"):
    frequency = frequency.lower()
    if frequency in ["d", "daily", "1"]:
        upd_guild = f"UPDATE Guild SET sendStatus = '1', chanStatID = {ctx.message.channel.id}, lastSend = CAST(NOW() AS DATE) WHERE idGuild = {ctx.guild.id};"

    elif frequency in ["w", "weekly", "2"]:
        upd_guild = f"UPDATE Guild SET sendStatus = '2', chanStatID = {ctx.message.channel.id}, lastSend = CAST(NOW() AS DATE) WHERE idGuild = {ctx.guild.id};"

    elif frequency in ["m", "monthly", "3"]:
        upd_guild = f"UPDATE Guild SET sendStatus = '3', chanStatID = {ctx.message.channel.id}, lastSend = CAST(NOW() AS DATE) WHERE idGuild = {ctx.guild.id};"

    elif frequency == "help":
        ctx.send("WIP")
        return

    else:
        await ctx.send("Sorry, but I don't recognize this frequency. \nRefers to the `help` parameter to see what I can do !")
        return 

    cursor.execute(upd_guild)
    cnx.commit()
    await ctx.send("Now this channel will receive your guild stats at the frequency you asked !")

@bot.command(description = "Stop receiving the server stats", aliases = ["UNSET"])
@commands.guild_only()
@commands.has_permissions(manage_channels = True)
async def unset(ctx):
    delete = f"UPDATE Guild SET chanStatID = NULL, sendStatus = '0' WHERE idGuild {ctx.guild.id};"
    cursor.execute(delete)
    cnx.commit()

    await ctx.send("This channel will no longer receive your server stats !")

@bot.command(aliases = ["usagechannel", "top_users", "usage_channel"], description = "Get the channel statistics")
@commands.guild_only()
async def usageChannel(ctx, limit : int = 5):
    chan = ctx.channel
    topMember = ""
    bottomMember = ""
    user = None
    date = chan.created_at.strftime("%D")

    select1 = f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongC WHERE idChannel = {chan.id}) FROM BelongC WHERE idChannel = {chan.id} ORDER BY numberMsg DESC LIMIT {limit};"
    select2 = f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongC WHERE idChannel = {chan.id}) FROM BelongC WHERE idChannel = {chan.id} ORDER BY numberMsg LIMIT {limit};"
    cursor.execute(select1)
    query1 = cursor.fetchall()

    for row in query1:
        user = bot.get_user(row[0])
        topMember += f"• {user.mention} : **{row[1]}**\n"

    cursor.execute(select2)
    query2 = cursor.fetchall()
    for row in query2:
        user = bot.get_user(row[0])
        bottomMember += f"• {user.mention} : **{row[1]}**\n"

    embed = discord.Embed(title = "Channel Statistics", description = f"Statistics of the channel **{chan.name}**", color = 0x0089FF)
    embed.set_thumbnail(url = ctx.guild.icon_url)
    embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
    embed.add_field(name = "Channel name :", value = chan.name)
    embed.add_field(name = "Channel creation date :", value = date)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = "Total messages sended :", value = row[2])
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = f"Top {len(query1)} users of this channel :", value = topMember)
    embed.add_field(name = f"Bottom {len(query2)} users of this channel :", value = bottomMember)
    await ctx.send(embed = embed)

@bot.command(description = "Reset your server data (channel, message_channel, reaction or server)", aliases = ["resetstat", "reset_stat"])
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def resetStat(ctx, data, channel_id : int = None):
    upd = ""
    data = data.lower()

    if data == "channel" or data == "chan":
        if channel_id == None:
            upd = f"UPDATE Channel SET numberMsg = 0 WHERE idGuild = {ctx.guild.id};"
        else:
            upd = f"UPDATE Channel SET numberMsg = 0 WHERE idGuild = {ctx.guild.id} AND idChannel = {channel_id};"

    elif data == "message_channel" or data == "msgchannel" or data == "msg_chan" or data == "msgchan":
        if channel_id == None:
            await ctx.send("Sorry but for this statistic, the ID of the channel is mandatory")
        else:
            upd = f"UPDATE BelongC SET numberMsg = 0 WHERE idChannel = {channel_id};"

    elif data == "reaction" or data == "react":
        upd = f"UPDATE Reaction set numberReact = 0 WHERE idGuild = {ctx.guild.id};"

    elif data == "guild" or data == "server":
        upd = f"UPDATE Guild SET newMembers = 0, lostMembers = 0 WHERE idGuild = {ctx.guild.id};"

    else:
        await ctx.send("Sorry, but I don't recognize this type")
        return

    cursor.execute(upd)
    cnx.commit()
    await ctx.send(f"Statistics __{data}__ successfully reseted !")

@bot.command(aliases = ["serverstats", "server_stats", "guildStats", "guild_stats"], description = "Get your server statistics")
@commands.guild_only()
async def serverStats(ctx):
    select = f"SELECT idGuild, chanStatID, newMembers, lostMembers, totalMembers, lastSend, keyWord, nbKeyWord FROM Guild WHERE idGuild = {ctx.guild.id};"
    cursor.execute(select)
    query = cursor.fetchall()

    embed = await getEmbedStat(ctx.guild, query[0])
    await ctx.send(embed = embed)

@bot.command(aliases = ["userstats", "user_stats", "memberStats", "member_stats"], description = "Get a user statistics")
async def userStats(ctx, id : int = None):
    if id == None:
        user = ctx.author
        prem = "Not in premium or data impossible"
    
    else:
        user = ctx.guild.get_member(id)

    dateU = user.created_at.strftime("%D")
    select = ""
    prem = ""

    if id != None and (not ctx.message.guild or user.premium_since == None):
        prem = "Not in premium"
    else:
        prem = str(user.premium_since)

    if not ctx.message.guild:
        select = f"""SELECT COUNT(idGuild), SUM(bg.numberMsg)
                     FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                     WHERE u.idUser = {user.id}"""

    else:
        selectVerif = f"SELECT idChannel FROM BelongC WHERE idUser = {user.id} AND idChannel = {ctx.channel.id};"
        cursor.execute(selectVerif)
        query = cursor.fetchall()

        if len(query) == 0:
            select = f"""SELECT COUNT(idGuild), SUM(bg.numberMsg), bg.nbSecond, 0
                         FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                         WHERE u.idUser = {user.id};"""

        else:
            select = f"""SELECT COUNT(idGuild), SUM(bg.numberMsg), bg.nbSecond, bc.numberMsg
                         FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                                     INNER JOIN BelongC bc ON u.idUser = bc.idUser
                         WHERE u.idUser = {user.id} AND bc.idChannel = {ctx.channel.id};"""

    cursor.execute(select)
    query = cursor.fetchall()

    embed = discord.Embed(title = "User statistics", description = f"Statistics of the user **{user}**", color = 0x0089FF)
    embed.set_thumbnail(url = user.avatar_url)
    embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
    embed.add_field(name = "Name of the user :", value = user.name)
    embed.add_field(name = "Discriminator :", value = user.discriminator)
    embed.add_field(name = "Display name :", value = user.display_name)
    embed.add_field(name = "Account creation date :", value = dateU)
    embed.add_field(name = "Premium since :", value = prem)
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)
    embed.add_field(name = "Total guilds registered :", value = query[0][0])
    embed.add_field(name = "Total messages in the server :", value = query[0][1])
    embed.add_field(name= '\u200B', value= '\u200B', inline= True)

    if ctx.message.guild:
        embed.add_field(name = "Total messages in the channel :", value = query[0][3])

        nbSec = query[0][2]
        if nbSec != None and nbSec != 0:
            hour = int(nbSec / 3600)
            nbSec -= 3600 * hour
            minute = int(nbSec / 60)
            nbSec - nbSec * minute
            embed.add_field(name = "Time passed in voice chat (hh:mm:ss) :", value = f"{hour}:{minute}:{nbSec}")

        else:
            embed.add_field(name = "Time passed in voice chat (hh:mm:ss) :", value = f"00:00:00")

    await ctx.send(embed = embed)

@bot.command(description = "Gives the top 10 users (limit can be changed) in a category (use help)", aliases = ["TOP"])
async def top(ctx, category, limit : int = 10):
    if limit < 1 or limit > 25:
        await ctx.send("This limit is forbidden, use a number between 1 and 25")

    res = f"Top {limit} users for the category {category}\n"
    category = category.lower()
    if category == "help":
        await ctx.send("""Categories available for the command : \n• `messages` \n• `voice_chat`""")
        return

    elif category == "messages":
        select = f"SELECT idUser, SUM(numberMsg) FROM BelongG GROUP BY idUser ORDER BY numberMsg DESC LIMIT {limit};"
        cursor.execute(select)
        query = cursor.fetchall()

        res += "Ordered by the total number of messages registered :\n"
        for id, nbre in query:
            user = bot.get_user(id)
            res += f"• {user.name}#{user.discriminator} ==> {nbre}\n"
        await ctx.send(res)

    elif category == "voice_chat":
        select = f"SELECT idUser, SUM(nbSecond) FROM BelongG GROUP BY idUser ORDER BY nbSecond DESC LIMIT {limit};"
        cursor.execute(select)
        query = cursor.fetchall()

        res += "Ordered by the total of time passed in voice chat (hh:mm:ss) :\n"
        for id, nbSec in query:
            if nbSec == None:
                nbSec = 0

            hour = int(nbSec / 3600)
            nbSec -= 3600 * hour
            minute = int(nbSec / 60)
            nbSec -= 60 * minute

            user = bot.get_user(id)
            res += f"• {user.name}#{user.discriminator} ==> {hour}:{minute}:{nbSec}\n"
        await ctx.send(res)
    
    else:
        await ctx.send("I don't recognize this category sorry, maybe you spelled it wrong, look at the `help` category to see more")

@bot.command(description = "Set the keyword of your server", aliases = ["setkeyword", "set_keyword"])
@commands.has_permissions(manage_channels = True)
@commands.guild_only()
async def setKeyword(ctx, word):
    if len(word) > 26:
        await ctx.send("Your word is too long to be registered in the database")
        return

    upd_guild = f"UPDATE Guild SET keyWord = '{word}', nbKeyWord = 0 WHERE idGuild = {ctx.guild.id};"
    cursor.execute(upd_guild)

    await ctx.send(f"The key-word **{word}** has been registered in the database")
    cnx.commit()

@bot.command(description = "Enable or disable the auto-add of the channels in the database when created", aliases = ["AUTOADD", "autoadd"])
@commands.has_permissions(manage_channels = True)
@commands.guild_only()
async def autoAdd(ctx):
    new = ""
    msg = ""
    cursor.execute(f"SELECT autoAdd FROM Guild WHERE idGuild = {ctx.guild.id};")
    value = cursor.fetchall()[0][0]

    if value == "0":
        new = "1"
        msg = "Enabled"
    else:
        new = "0"
        msg = "Disabled"

    cursor.execute(f"UPDATE Guild SET autoAdd = '{new}' WHERE idGuild = {ctx.guild.id};")
    cnx.commit()
    await ctx.send("Auto-add set to " + msg)

@bot.command(description = "Reload the users in your guild (useful if the bot got disconnected)", aliases = ["loadusers", "load_users"])
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def loadUsers(ctx):
    for member in ctx.guild.members:
        if not member.bot:
            select = f"SELECT idUser FROM User WHERE idUser = {member.id};"
            cursor.execute(select)

            if len(cursor.fetchall()) == 0:
                add_user = f"INSERT INTO User (idUser, yearDate) VALUES ({member.id}, {member.created_at.year});"
                add_belong = f"INSERT INTO BelongG VALUES({member.id}, {ctx.guild.id}, 0, 0);"
                upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {ctx.guild.id};"

                cursor.execute(add_user)
                cursor.execute(add_belong)
                cursor.execute(upd_guild)

    cnx.commit()
    await ctx.send("Users loaded in the database !")

@bot.command(description = "Load your server data (useful if the bot got disconnected when you added it)", aliases = ["load_Guild", "loadserver", "loadguild"])
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def loadServer(ctx):
    res = await loadG(ctx.guild)
    if not res:
        await ctx.send("Server already added to database")

@bot.command(description = "Load your server custom emotes (useful if the bot got disconnected)", aliases = ["loademote", "loademoji", "load_emoji", "load_emote"])
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def loadEmote(ctx):
    for emoji in ctx.guild.emojis:
        add_emoji = "INSERT IGNORE Reaction VALUES(%s, %s, %s, %s);"
        data_emoji = (emoji.id, ctx.guild.id, 0, emoji.name)
        cursor.execute(add_emoji, data_emoji)

    cnx.commit()
    await ctx.send("Reactions successfully loaded !")

@bot.command(description = "Load all the channels where I have an access (useful if the bot got disconnected)", aliases = ["loadchannels", "loadchan", "loadchannel"])
@commands.guild_only()
@commands.has_permissions(administrator = True)
async def loadChannels(ctx):
    me = ctx.guild.get_member(713164137194061916)
    for channel in ctx.guild.text_channels:
        if channel.permissions_for(me).read_messages == True:
            addChan = "INSERT IGNORE Channel(idChannel, idGuild) VALUES(%s, %s);"
            dataChan = (channel.id, ctx.guild.id)
            cursor.execute(addChan, dataChan)
    
    cnx.commit()
    await ctx.send("Channels successfully loaded !")

# Envoi des stats

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

# Lancement bot

bot.run(TOKEN)