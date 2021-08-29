import discord
from discord.ext import commands

def setup(bot, cursor, cnx):
    bot.add_cog(Admin(bot, cursor, cnx))

class Admin(commands.Cog):
    def __init__(self, bot, cursor, cnx) -> None:
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.command(description = "Set the keyword of your server", aliases = ["setkeyword", "set_keyword"])
    @commands.has_permissions(manage_channels = True)
    @commands.guild_only()
    async def setKeyword(self, ctx, word):
        if len(word) > 26:
            await ctx.send("Your word is too long to be registered in the database")
            return

        upd_guild = f"UPDATE Guild SET keyWord = '{word}', nbKeyWord = 0 WHERE idGuild = {ctx.guild.id};"
        self.cursor.execute(upd_guild)

        await ctx.send(f"The key-word **{word}** has been registered in the database")
        self.cnx.commit()

    @commands.command(description = "Enable or disable the auto-add of the channels in the database when created", aliases = ["AUTOADD", "autoadd"])
    @commands.has_permissions(manage_channels = True)
    @commands.guild_only()
    async def autoAdd(self, ctx):
        new = ""
        msg = ""
        self.cursor.execute(f"SELECT autoAdd FROM Guild WHERE idGuild = {ctx.guild.id};")
        value = self.cursor.fetchall()[0][0]

        if value == "0":
            new = "1"
            msg = "Enabled"
        else:
            new = "0"
            msg = "Disabled"

        self.cursor.execute(f"UPDATE Guild SET autoAdd = '{new}' WHERE idGuild = {ctx.guild.id};")
        self.cnx.commit()
        await ctx.send("Auto-add set to " + msg)

    @commands.command(description = "Reload the users in your guild (useful if the bot got disconnected)", aliases = ["loadusers", "load_users"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadUsers(self, ctx):
        for member in ctx.guild.members:
            if not member.bot:
                select = f"SELECT idUser FROM User WHERE idUser = {member.id};"
                self.cursor.execute(select)

                if len(self.cursor.fetchall()) == 0:
                    add_user = f"INSERT INTO User (idUser, yearDate) VALUES ({member.id}, {member.created_at.year});"
                    add_belong = f"INSERT INTO BelongG VALUES({member.id}, {ctx.guild.id}, 0, 0);"
                    upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {ctx.guild.id};"

                    self.cursor.execute(add_user)
                    self.cursor.execute(add_belong)
                    self.cursor.execute(upd_guild)

        self.cnx.commit()
        await ctx.send("Users loaded in the database !")

    @commands.command(description = "Load your server data (useful if the bot got disconnected when you added it)", aliases = ["load_Guild", "loadserver", "loadguild"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadServer(self, ctx):
        select = f"SELECT idGuild FROM Guild WHERE idGuild = {ctx.guild.id};"
        self.cursor.execute(select)
        if len(self.cursor.fetchall()) > 0:
            print("Server already loaded in the database")
            return

        members = ctx.guild.members
        count = 0
        for member in members:
            if not member.bot:
                count += 1

                add_user = f"INSERT IGNORE User VALUES({member.id}, {member.created_at.year})"
                self.cursor.execute(add_user)

        add_guild = "INSERT INTO Guild(idGuild, totalMembers) VALUES(%s, %s);"
        data_guild = (ctx.guild.id, count)
        self.cursor.execute(add_guild, data_guild)

        for chan in ctx.guild.text_channels:
            add_chan = "INSERT INTO Channel VALUES(%s, %s, %s);"
            data_chan = (chan.id, ctx.guild.id, 0)
            self.cursor.execute(add_chan, data_chan)

        for emoji in ctx.guild.emojis:
            add_emoji = "INSERT INTO Reaction VALUES(%s, %s, %s, %s);"
            data_emoji = (emoji.id, ctx.guild.id, 0, emoji.name)
            self.cursor.execute(add_emoji, data_emoji)

        updG = f"UPDATE Guild SET newMembers = newMembers + {count}, totalMembers = totalMembers + {count} WHERE idGuild = {ctx.guild.id};"
        self.cursor.execute(updG)
        self.cnx.commit()
        print("Server successfully loaded !")

    @commands.command(description = "Load your server custom emotes (useful if the bot got disconnected)", aliases = ["loademote", "loademoji", "load_emoji", "load_emote"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadEmote(self, ctx):
        for emoji in ctx.guild.emojis:
            add_emoji = "INSERT IGNORE Reaction VALUES(%s, %s, %s, %s);"
            data_emoji = (emoji.id, ctx.guild.id, 0, emoji.name)
            self.cursor.execute(add_emoji, data_emoji)

        self.cnx.commit()
        await ctx.send("Reactions successfully loaded !")

    @commands.command(description = "Load all the channels where I have an access (useful if the bot got disconnected)", aliases = ["loadchannels", "loadchan", "loadchannel"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadChannels(self, ctx):
        me = ctx.guild.get_member(713164137194061916)
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(me).read_messages == True:
                addChan = "INSERT IGNORE Channel(idChannel, idGuild) VALUES(%s, %s);"
                dataChan = (channel.id, ctx.guild.id)
                self.cursor.execute(addChan, dataChan)
        
        self.cnx.commit()
        await ctx.send("Channels successfully loaded !")

    @commands.command(description = "Reset your server data (channel, message_channel, reaction or server)", aliases = ["resetstat", "reset_stat"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def resetStat(self, ctx, data, channel_id : int = None):
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

        self.cursor.execute(upd)
        self.cnx.commit()
        await ctx.send(f"Statistics __{data}__ successfully reseted !")

    @commands.command(description = "Stop receiving the server stats", aliases = ["UNSET"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def unset(self, ctx):
        delete = f"UPDATE Guild SET chanStatID = NULL, sendStatus = '0' WHERE idGuild {ctx.guild.id};"
        self.cursor.execute(delete)
        self.cnx.commit()

        await ctx.send("This channel will no longer receive your server stats !")

    @commands.command(description = "Set the frequency you want to receive your server stats", aliases = ["set", "SET", "setstats"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def setStats(self, ctx, frequency = "daily"):
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

        self.cursor.execute(upd_guild)
        self.cnx.commit()
        await ctx.send("Now this channel will receive your guild stats at the frequency you asked !")