import discord
from discord.ext import commands
from database.database import DatabaseHandler

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB = DatabaseHandler()

    def loadU(self, ctx) -> None:
        members = ctx.guild.members
        count = 0
        for member in members:
            if not member.bot:
                if len(self.DB.getUser(member.id)) > 0:
                    self.DB.newUser(member.id, ctx.guild.id, member.created_at.year, False)
                    count += 1
        self.DB.updNewMembers(ctx.guild.id, count)

    def loadC(self, ctx) -> None:
        me = ctx.guild.get_member(713164137194061916)
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(me).read_messages == True:
                self.DB.addChannel(channel.id, ctx.guild.id, False)
        self.DB.commitQ()

    def loadR(self, ctx) -> None:
        for emoji in ctx.guild.emojis:
            self.DB.addReact(emoji.id, ctx.guild.id, emoji.name, False)
        self.DB.commitQ()


    @commands.command(description = "Set the keyword of your server", aliases = ["setkeyword", "set_keyword"])
    @commands.has_permissions(manage_channels = True)
    @commands.guild_only()
    async def setKeyword(self, ctx, word):
        if len(word) > 26:
            await ctx.send("Your word is too long to be registered in the database")
            return

        self.DB.updKeyWord(word, ctx.guild.id)
        await ctx.send(f"The key-word **{word}** has been registered in the database")

    @commands.command(description = "Enable or disable the auto-add of the channels in the database when created", aliases = ["AUTOADD", "autoadd"])
    @commands.has_permissions(manage_channels = True)
    @commands.guild_only()
    async def autoAdd(self, ctx):
        new = ""
        msg = ""
        value = self.DB.getGuild(ctx.guild.id)[0][9]

        if value == "0":
            new = "1"
            msg = "Enabled"
        else:
            new = "0"
            msg = "Disabled"

        self.DB.updAdd(new, ctx.guild.id)
        await ctx.send("Auto-add set to " + msg)

    @commands.command(description = "Load your server data (useful if the bot got disconnected when you added it)", aliases = ["load_Guild", "loadserver", "loadguild"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadServer(self, ctx):
        if len(self.DB.getGuild(ctx.guild.id)) > 0:
            print("Server already loaded in the database")
            return

        self.loadU(ctx)
        self.loadC(ctx)
        self.loadR(ctx)
        print("Server successfully loaded !")

    @commands.command(description = "Reload the users in your guild (useful if the bot got disconnected)", aliases = ["loadusers", "load_users"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadUsers(self, ctx):
        self.loadU(ctx)
        await ctx.send("Users loaded in the database !")

    @commands.command(description = "Load all the channels where I have an access (useful if the bot got disconnected)", aliases = ["loadchannels", "loadchan", "loadchannel"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadChannels(self, ctx):
        self.loadC(ctx)
        await ctx.send("Channels successfully loaded !")

    @commands.command(description = "Load your server custom emotes (useful if the bot got disconnected)", aliases = ["loademote", "loademoji", "load_emoji", "load_emote"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadEmote(self, ctx):
        self.loadR(ctx)
        await ctx.send("Emotes successfully loaded !")

    @commands.command(description = "Reset your server data (channel, message_channel, reaction or server)", aliases = ["resetstat", "reset_stat"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def resetStat(self, ctx, data, channelID : int = None):
        data = data.lower()

        if data == "channel" or data == "chan":
            self.DB.resetChannel(ctx.guild.id, channelID)

        elif data == "message_channel" or data == "msgchannel" or data == "msg_chan" or data == "msgchan":
            self.DB.resetMsgChan(channelID)

        elif data == "reaction" or data == "react":
            self.DB.resetReact(ctx.guild.id)

        elif data == "guild" or data == "server":
            self.DB.resetGuild()

        else:
            await ctx.send("Data possible : `channel` (provide the id to reset a specific a channel instead of all the text channels)\n`message_channel` \n `reaction` \n`server`")
            return

        await ctx.send(f"Statistics __{data}__ successfully reseted !")

    @commands.command(description = "Set the frequency you want to receive your server stats", aliases = ["set", "SET", "setstats"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def setStats(self, ctx, frequency = "daily"):
        frequency = frequency.lower()
        status = ""

        if frequency in ["d", "daily", "1"]:
            status = "1"

        elif frequency in ["w", "weekly", "2"]:
            status = "2"

        elif frequency in ["m", "monthly", "3"]:
            status = "3"

        elif frequency == "help":
            ctx.send("WIP")
            return

        else:
            await ctx.send("Sorry, but I don't recognize this frequency. \nRefers to the `help` parameter to see what I can do !")
            return 

        self.DB.setSend(ctx.guild.id, ctx.message.channel.id, status)
        await ctx.send("Now this channel will receive your guild stats at the frequency you asked !")

    @commands.command(description = "Stop receiving the server stats", aliases = ["UNSET"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def unset(self, ctx):
        self.DB.unsetSend(ctx.guild.id)
        await ctx.send("This channel will no longer receive your server stats !")

    @commands.command(description = "Erase the channel from the database", aliases = ["erasechannel", "erase_channel"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def eraseChannel(self, ctx, id : int):
        if id is None:
            await ctx.send("You need to provide the channel id to make sure you want to delete it")
        
        elif id != ctx.channel.id:
            await ctx.send("The id needs to be equal to this current channel !")

        else:
            self.DB.deleteChannel(id)

"""
    @commands.command(description = "Hide the channel to me", aliases = ["HIDE"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def hide(self, ctx):
        print(self.bot.get_user(713164137194061916))
        print(ctx.channel.permissions_for(self.bot.get_user(237657579692621824)))

        await ctx.channel.set_permissions(target = self.bot.user, read_messages = False,
                                                                  send_messages = False)
"""
def setup(bot):
    bot.add_cog(Admin(bot))