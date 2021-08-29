import discord
from discord.ext import commands
import datetime as dt
import matplotlib
import matplotlib.pyplot as plt
import os

def setup(bot, cursor, cnx):
    bot.add_cog(Stats(bot, cursor))

class Stats(commands.Cog):
    def __init__(self, bot, cursor):
        self.bot = bot
        self.cursor = cursor

    @commands.command(description = "See the amount of discord account created each year in your server", aliases = ["dateaccounts", "dates_accounts"])
    @commands.guild_only()
    async def dateAccounts(self, ctx):
        dates = {}
        year = int(dt.datetime.now().strftime("%Y"))
                    
        for i in range(2015, year + 1):
            dates[i] = 0
            select = f"SELECT COUNT(yearDate) FROM BelongG bg INNER JOIN User u ON bg.idUser = u.idUser WHERE yearDate = {i} AND bg.idGuild = {ctx.guild.id};"
            self.cursor.execute(select)
            query = self.cursor.fetchall()
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

    @commands.command(aliases = ["guildInfo", "server_info"], description = "Your server data")
    @commands.guild_only()
    async def serverInfo(self, ctx):
        server = ctx.guild

        select = f"SELECT COUNT(idUser) FROM BelongG WHERE idGuild = {server.id};"
        self.cursor.execute(select)

        embed = discord.Embed(title = "Guild's infos", description = "Your guild informations !", color = 0x0089FF)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = server.icon_url)
        embed.add_field(name = "Name :", value = server.name, inline = True)
        embed.add_field(name = "Owner :", value = server.owner, inline = True)
        embed.add_field(name = "Region :", value = server.region, inline = True)
        embed.add_field(name = "Total users :", value = len(server.members), inline = True)
        embed.add_field(name = "Total registered users :", value = self.cursor.fetchall()[0][0], inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "Total of text channels :", value = len(server.text_channels), inline = True)
        embed.add_field(name = "Total of voice channels :", value = len(server.voice_channels), inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "Total of emojis :", value = len(server.emojis), inline = True)
        embed.add_field(name = "Total of roles :", value = len(server.roles), inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)

        await ctx.send(embed = embed)

    @commands.command(aliases = ["usagechannel", "top_users", "usage_channel"], description = "Get the channel statistics")
    @commands.guild_only()
    async def usageChannel(self, ctx, limit : int = 5):
        chan = ctx.channel
        topMember = ""
        bottomMember = ""
        user = None
        date = chan.created_at.strftime("%D")

        select1 = f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongC WHERE idChannel = {chan.id}) FROM BelongC WHERE idChannel = {chan.id} ORDER BY numberMsg DESC LIMIT {limit};"
        select2 = f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongC WHERE idChannel = {chan.id}) FROM BelongC WHERE idChannel = {chan.id} ORDER BY numberMsg LIMIT {limit};"
        self.cursor.execute(select1)
        query1 = self.cursor.fetchall()

        for row in query1:
            user = self.bot.get_user(row[0])
            topMember += f"• {user.mention} : **{row[1]}**\n"

        self.cursor.execute(select2)
        query2 = self.cursor.fetchall()
        for row in query2:
            user = self.bot.get_user(row[0])
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

    @commands.command(aliases = ["serverstats", "server_stats", "guildStats", "guild_stats"], description = "Get your server statistics")
    @commands.guild_only()
    async def serverStats(self, ctx):
        select = f"SELECT idGuild, chanStatID, newMembers, lostMembers, totalMembers, lastSend, keyWord, nbKeyWord FROM Guild WHERE idGuild = {ctx.guild.id};"
        self.cursor.execute(select)
        query = self.cursor.fetchall()

        embed = await self.getEmbedStat(ctx.guild, query[0])
        await ctx.send(embed = embed)

    @commands.command(aliases = ["userstats", "user_stats", "memberStats", "member_stats"], description = "Get a user statistics")
    async def userStats(self, ctx, id : int = None):
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
            self.cursor.execute(selectVerif)
            query = self.cursor.fetchall()

            if len(query) == 0:
                select = f"""SELECT COUNT(idGuild), SUM(bg.numberMsg), bg.nbSecond, 0
                            FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                            WHERE u.idUser = {user.id};"""

            else:
                select = f"""SELECT COUNT(idGuild), SUM(bg.numberMsg), bg.nbSecond, bc.numberMsg
                            FROM User u INNER JOIN BelongG bg ON u.idUser = bg.idUser
                                        INNER JOIN BelongC bc ON u.idUser = bc.idUser
                            WHERE u.idUser = {user.id} AND bc.idChannel = {ctx.channel.id};"""

        self.cursor.execute(select)
        query = self.cursor.fetchall()

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

    @commands.command(description = "Gives the top 10 users (limit can be changed) in a category (use help)", aliases = ["TOP"])
    async def top(self, ctx, category, limit : int = 10):
        if limit < 1 or limit > 25:
            await ctx.send("This limit is forbidden, use a number between 1 and 25")

        res = f"Top {limit} users for the category {category}\n"
        category = category.lower()
        if category == "help":
            await ctx.send("""Categories available for the command : \n• `messages` \n• `voice_chat`""")
            return

        elif category == "messages":
            select = f"SELECT idUser, SUM(numberMsg) FROM BelongG GROUP BY idUser ORDER BY numberMsg DESC LIMIT {limit};"
            self.cursor.execute(select)
            query = self.cursor.fetchall()

            res += "Ordered by the total number of messages registered :\n"
            for id, nbre in query:
                user = self.bot.get_user(id)
                res += f"• {user.name}#{user.discriminator} ==> {nbre}\n"
            await ctx.send(res)

        elif category == "voice_chat":
            select = f"SELECT idUser, SUM(nbSecond) FROM BelongG GROUP BY idUser ORDER BY nbSecond DESC LIMIT {limit};"
            self.cursor.execute(select)
            query = self.cursor.fetchall()

            res += "Ordered by the total of time passed in voice chat (hh:mm:ss) :\n"
            for id, nbSec in query:
                if nbSec == None:
                    nbSec = 0

                hour = int(nbSec / 3600)
                nbSec -= 3600 * hour
                minute = int(nbSec / 60)
                nbSec -= 60 * minute

                user = self.bot.get_user(id)
                res += f"• {user.name}#{user.discriminator} ==> {hour}:{minute}:{nbSec}\n"
            await ctx.send(res)
        
        else:
            await ctx.send("I don't recognize this category sorry, maybe you spelled it wrong, look at the `help` category to see more")

    async def getEmbedStat(self, guild : discord.Guild, row = None) -> discord.Embed:
        selectM = f"SELECT idUser, numberMsg, (SELECT SUM(numberMsg) FROM BelongG WHERE idGuild = {guild.id}) FROM BelongG WHERE idGuild = {guild.id} ORDER BY numberMsg DESC LIMIT 5;"
        selectR = f"SELECT idReact, nameReact, numberReact, (SELECT SUM(numberReact) FROM Reaction WHERE idGuild = {guild.id}) FROM reaction WHERE idGuild = {guild.id} ORDER BY numberReact DESC LIMIT 5;"
        selectC = f"SELECT idChannel, numberMsg FROM Channel WHERE idGuild = {guild.id} ORDER BY numberMsg DESC LIMIT 5;"

        self.cursor.execute(selectM)
        topMember = ""
        for id, number, totalM in self.cursor.fetchall():
            user = self.bot.get_user(id)

            if user == None:
                delUser = f"DELETE FROM BelongG WHERE idUser = {id} AND idGuild = {guild.id};"
                self.cursor.execute(delUser)
            else:
                topMember += f"{user.mention} : **{number}**\n"

        self.cursor.execute(selectR)
        topReact = ""
        for id, name, number, totalR in self.cursor.fetchall():
            emoji = self.bot.get_emoji(id)

            if emoji == None:
                delEmoji = f"DELETE FROM Reaction WHERE idReact = {id};"
                self.cursor.execute(delEmoji)
            else:
                topReact += f"<:{name}:{id}> : **{number}**\n"

        self.cursor.execute(selectC)
        topChan = ""
        for id, number in self.cursor.fetchall():
            chan = self.bot.get_channel(id)

            if chan == None:
                delBC = f"DELETE FROM BelongC WHERE idChan = {id};"
                delChan = f"DELETE FROM Channel WHERE idChan = {id};"
                self.cursor.execute(delBC)
                self.cursor.execute(delChan)
            else:
                topChan += f"<#{id}> : **{number}**\n"

        resKW = ""
        if row[6] == "":
            resKW = "No key-word"
        else:
            resKW = row[7]

        embed = discord.Embed(title = f"Statistics of the server {guild.name}", description = f"Last send : {row[5]}", color = 0x0089FF)
        embed.set_author(name = self.bot.user, icon_url = self.bot.user.avatar_url)
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