import discord
from discord.enums import UserFlags
from discord.ext import commands
import datetime as dt
from database.database import DatabaseHandler

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB = DatabaseHandler()

    async def getEmbedStat(self, guild : discord.Guild, row = None) -> discord.Embed:
        queryM, queryR, queryC = self.DB.embedStat(guild)
        topMember = ""

        for id, number, totalM in queryM:
            user = self.bot.get_user(id)
            if user == None:
                self.DB.deleteBG(id, 0)
            else:
                topMember += f"{user.mention} : **{number}**\n"

        topReact = ""
        for id, name, number, totalR in queryR:
            emoji = self.bot.get_emoji(id)
            if emoji == None:
                self.DB.deleteReact(id)
            else:
                topReact += f"<:{name}:{id}> : **{number}**\n"

        topChan = ""
        for id, number in queryC:
            chan = self.bot.get_channel(id)
            if chan == None:
                self.DB.deleteChan(id)
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
        embed.add_field(name = "Total members :", value = row[3])
        embed.add_field(name = "New members :", value = row[1])
        embed.add_field(name = "Lost members :", value = row[2])
        # Count
        embed.add_field(name = "Total messages send", value = totalM)
        embed.add_field(name = "Total usage of the key word", value = resKW)
        embed.add_field(name = "Total reactions used", value = totalR)
        # Top
        embed.add_field(name = "Top active members :", value = topMember)
        embed.add_field(name = "Top active channels :", value = topChan)
        embed.add_field(name = "Top used reactions :", value = topReact)
        return embed

    @commands.command(description = "See the amount of discord account created each year in your server", aliases = ["dateaccounts", "dates_accounts"])
    @commands.guild_only()
    async def dateAccounts(self, ctx):
        dates = {}
        total = 0
        baseStr = "[----------]"
        year = int(dt.datetime.now().strftime("%Y"))
                    
        for i in range(2015, year + 1):
            dates[i] = 0
            query = self.DB.getYearCount(i, ctx.guild.id)
            if len(query) != 0:
                count = query[0][0]
                dates[i] += count
                total += count
        
        embed = discord.Embed(title = "Accounts statistic", description = "Number of accounts created per year in the server", color = 0x0089FF)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = self.bot.user.avatar_url)
        for year in dates:
            if dates[year] > 0:
                percent = round((dates[year] / total) * 100, 2)
                index = int(round((percent / 10), 0))
                newStr = baseStr.replace("-", "/", index)
                embed.add_field(name = year,
                                value = newStr[:1] + "**" + newStr[1:index + 1] + "**" + newStr[index + 1:] + f" ==> **{percent}** %",
                                inline = False)
            else:
                embed.add_field(name = year, value = baseStr + " ==> **0** %", inline = False)
        await ctx.send(embed = embed)

    @commands.command(aliases = ["guildInfo", "server_info"], description = "Your server data")
    @commands.guild_only()
    async def serverInfo(self, ctx):
        server = ctx.guild
        users = self.DB.countUserGuild(server.id)

        embed = discord.Embed(title = "Server's infos", description = "Your server informations !", color = 0x0089FF)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = server.icon_url)
        embed.add_field(name = "Name :", value = server.name, inline = True)
        embed.add_field(name = "Owner :", value = server.owner, inline = True)
        embed.add_field(name = "Region :", value = server.region, inline = True)
        embed.add_field(name = "Total users :", value = len(server.members), inline = True)
        embed.add_field(name = "Total registered users :", value = users, inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "Total of text channels :", value = len(server.text_channels), inline = True)
        embed.add_field(name = "Total of voice channels :", value = len(server.voice_channels), inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "Total of emojis :", value = len(server.emojis), inline = True)
        embed.add_field(name = "Total of roles :", value = len(server.roles), inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)

        await ctx.send(embed = embed)

    @commands.command(aliases = ["channelstats", "channel_stats"], description = "Get the channel statistics")
    @commands.guild_only()
    async def channelStats(self, ctx, limit : int = 5):
        chan = ctx.channel
        topMember = ""
        bottomMember = ""
        user = None
        date = chan.created_at.strftime("%D")

        top, bottom = self.DB.getUsageChannel(chan.id, limit)
        for row in top:
            user = self.bot.get_user(row[0])
            if user == None:
                self.DB.deleteBG(row[0], 0)
            else:
                topMember += f"• {user.mention} : **{row[1]}**\n"

        for row in bottom:
            user = self.bot.get_user(row[0])
            if user == None:
                self.DB.deleteBG(row[0], 0)
            else:
                bottomMember += f"• {user.mention} : **{row[1]}**\n"


        embed = discord.Embed(title = "Channel Statistics", description = f"Statistics of the channel **{chan.name}**", color = 0x0089FF)
        embed.set_thumbnail(url = ctx.guild.icon_url)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.add_field(name = "Channel name :", value = chan.name)
        embed.add_field(name = "Channel creation date :", value = date)
        embed.add_field(name= '\u200B', value= '\u200B', inline = True)
        embed.add_field(name = "Total messages sended :", value = row[2])
        embed.add_field(name= '\u200B', value= '\u200B', inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline = True)
        embed.add_field(name = f"Top {len(top)} users of this channel :", value = topMember)
        embed.add_field(name = f"Bottom {len(bottom)} users of this channel :", value = bottomMember)
        await ctx.send(embed = embed)

    @commands.command(aliases = ["serverstats", "server_stats", "guildStats", "guild_stats"], description = "Get your server statistics")
    @commands.guild_only()
    async def serverStats(self, ctx):
        query = self.DB.getGuild(ctx.guild.id)
        embed = await self.getEmbedStat(ctx.guild, query[0])
        await ctx.send(embed = embed)

    @commands.command(aliases = ["userstats", "user_stats", "memberStats", "member_stats"], description = "Get a user statistics")
    async def userStats(self, ctx, id : int = None):
        flags = {UserFlags.staff : "staff",
                 UserFlags.partner : "partner",
                 UserFlags.hypesquad : "hypesquad",
                 UserFlags.bug_hunter : "bug_hunter",
                 UserFlags.mfa_sms : "mfa_sms",
                 UserFlags.premium_promo_dismissed : "premium_promo_dismissed",
                 UserFlags.hypesquad_bravery : "hypesquad_bravery",
                 UserFlags.hypesquad_brilliance : "hypesquad_brilliance",
                 UserFlags.hypesquad_balance : "hypesquad_balance",
                 UserFlags.early_supporter : "early_supporter",
                 UserFlags.team_user : "team_user",
                 UserFlags.system : "system",
                 UserFlags.has_unread_urgent_messages : "has_unread_urgent_messages",
                 UserFlags.bug_hunter_level_2 : "bug_hunter_level_2",
                 UserFlags.verified_bot : "verified_bot",
                 UserFlags.verified_bot_developer : "verified_bot_developer"}

        if id == None:
            user = ctx.author
            prem = "Not in premium or data impossible"
        else:
            user = ctx.guild.get_member(id)
            if user == None:
                await ctx.send("This user doesn't exist")
                return

        dateU = user.created_at.strftime("%D")
        prem = ""

        if id != None and (not ctx.message.guild or user.premium_since == None):
            prem = str(user.premium_since)
        else:
            prem = "Not in premium"
            
        if not ctx.message.guild:
            query = self.DB.userMsg(user.id)
        else:
            if len(self.DB.getBC(user.id, 2, ctx.channel.id)) == 0:
                query = self.DB.userMsgChan(user.id, False)
            else:
                query = self.DB.userMsgChan(user.id, True, ctx.channel.id)

        badges = ""
        for value in user.public_flags.all():
            badges += flags[value] + ", "
        if len(badges) == 0:
            badges = "None"
        else:
            badges = badges[:len(badges) - 2]

        embed = discord.Embed(title = "User statistics", description = f"Statistics of the user **{user}**", color = 0x0089FF)
        embed.set_thumbnail(url = user.avatar_url)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.add_field(name = "Name of the user :", value = user.name)
        embed.add_field(name = "Discriminator :", value = user.discriminator)
        embed.add_field(name = "Display name :", value = user.display_name)
        embed.add_field(name = "Account creation date :", value = dateU)
        embed.add_field(name = "Premium since :", value = prem)
        embed.add_field(name= "Badges", value = badges, inline = True)
        embed.add_field(name = "Total guilds registered :", value = query[0][0])
        embed.add_field(name = "Total messages in the server :", value = query[0][1])
        embed.add_field(name= '\u200B', value= '\u200B', inline = True)

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
            query = self.DB.topMessages(limit)
            res += "Ordered by the total number of messages registered :\n"
            for id, nbre in query:
                user = self.bot.get_user(id)
                res += f"• {user.name}#{user.discriminator} ==> {nbre}\n"
            await ctx.send(res)

        elif category == "voice_chat":
            query = self.DB.topVoiceChat(limit)
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

        elif category in ["reaction", "reactions", "react"]:
            #query = self.DB.topReact(limit)
            await ctx.send("WIP")
        
        else:
            await ctx.send("I don't recognize this category sorry, maybe you spelled it wrong, look at the `help` category to see more")

    @commands.command(description = "Get the activity of the user on all the channels in the server", aliases = ["useractivity", "user_activity"])
    @commands.guild_only()
    async def userActivity(self, ctx, idUser : int = None):
        user = None
        if idUser == None:
            user = ctx.author
        else:
            user = self.bot.get_user(idUser)

        res = ""
        query = self.DB.activity(user.id, ctx.guild.id)
        for row in query:
            chan = self.bot.get_channel(row[0])
            if chan == None:
                self.DB.deleteChan(row[0])
            else:
                res += f"• {chan.mention} -> {row[1]} message(s)\n"
        embed = discord.Embed(title = "User's activity", description = f"Activity of the user {user} in the server {ctx.guild.name}", color = 0x0089FF)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = ctx.guild.icon_url)
        embed.add_field(name = "Activity :", value = res)
        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(Stats(bot))