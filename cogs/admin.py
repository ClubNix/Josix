import discord
from discord.ext import commands
from database.database import DatabaseHandler

class Admin(commands.Cog):
    """
    Cog Admin

    Regroup all the methods related to the administration.
    The managers of the server. They can extract data from the database or modify it.
    """

    def __init__(self, bot):
        """
        Initialize the bot given by the setup function
        Get the DB instance (same as the one created in the index)
        """

        self.bot = bot
        self.DB = DatabaseHandler()


    def loadU(self, ctx) -> None:
        """
        Load all the users in the server
        Update the DB with the new informations
        """

        members = ctx.guild.members
        count = 0
        for member in members:
            if not member.bot:
                if len(self.DB.getUser(member.id)) > 0:
                    self.DB.newUser(member.id, ctx.guild.id, member.created_at.year, False)
                    count += 1
        self.DB.updNewMembers(ctx.guild.id, count)


    def loadC(self, ctx) -> None:
        """
        Load all the channels in the server
        Update the DB with the new informations
        """

        me = ctx.guild.get_member(713164137194061916)
        for channel in ctx.guild.text_channels:
            if channel.permissions_for(me).read_messages == True:
                self.DB.addChannel(channel.id, ctx.guild.id, False)
        self.DB.commitQ()


    def loadR(self, ctx) -> None:
        """
        Load all the emojis (for the reactions) in the server
        Update the DB with the new informations
        """

        for emoji in ctx.guild.emojis:
            self.DB.addReact(emoji.id, ctx.guild.id, emoji.name, False)
        self.DB.commitQ()


    @commands.command(description = "Set the keyword of your server", aliases = ["setkeyword", "set_keyword"])
    @commands.has_permissions(manage_channels = True)
    @commands.guild_only()
    async def setKeyword(self, ctx, word):
        """
        Set the custom key-word of the server
        The word can't be more than 26 characters
        """

        if len(word) > 26:
            await ctx.send("Your word is too long to be registered in the database")
            return

        self.DB.updKeyWord(word, ctx.guild.id)
        await ctx.send(f"The key-word **{word}** has been registered in the database")


    @commands.command(description = "Enable or disable the auto-add of the channels in the database when created", aliases = ["AUTOADD", "autoadd"])
    @commands.has_permissions(manage_channels = True)
    @commands.guild_only()
    async def autoAdd(self, ctx):
        """
        To manage the auto-add of the channeks in the DB
        If disabled, an admin has to add it manually
        """

        new = ""
        msg = ""

        # Get the state of the autoAdd (0 for disable, 1 for enable)
        if self.DB.getGuild(ctx.guild.id)[0][9] == "0":
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
        """
        load all the informations about the server 
        Same as using loadUsers, loadChannels, loadEmotes one by one
        """

        self.loadU(ctx)
        self.loadC(ctx)
        self.loadR(ctx)
        print("Server successfully loaded !")


    @commands.command(description = "Reload the users in your guild (useful if the bot got disconnected)", aliases = ["loadusers", "load_users"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadUsers(self, ctx):
        """
        Load all the users
        """

        self.loadU(ctx)
        await ctx.send("Users loaded in the database !")


    @commands.command(description = "Load all the channels where I have an access (useful if the bot got disconnected)", aliases = ["loadchannels", "loadchan", "loadchannel"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadChannels(self, ctx):
        """
        Load all the channels
        """

        self.loadC(ctx)
        await ctx.send("Channels successfully loaded !")


    @commands.command(description = "Load your server custom emotes (useful if the bot got disconnected)", aliases = ["loademotes", "loademojis", "load_emojis", "load_emotes"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def loadEmotes(self, ctx):
        """
        Load all the emotes (for the reactions)
        """

        self.loadR(ctx)
        await ctx.send("Emotes successfully loaded !")


    @commands.command(description = "Reset your server data (channel, message_channel, reaction or server)", aliases = ["resetstat", "reset_stat"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def resetStat(self, ctx, data, channelID : int = None):
        """
        reset the stats of the specified field. (data parameter)
        To reset a channel, the ID id needed
        """

        data = data.lower()

        if data == "channel" or data == "chan":
            self.DB.resetChannel(ctx.guild.id, channelID) # reset the channel stats

        elif data == "message_channel" or data == "msgchannel" or data == "msg_chan" or data == "msgchan":
            self.DB.resetMsgChan(channelID) # reset the messages stats of the channel

        elif data == "reaction" or data == "react":
            self.DB.resetReact(ctx.guild.id) # reset the reaction stats

        elif data == "guild" or data == "server":
            self.DB.resetGuild() # reset the server stats 

        else:
            await ctx.send("Data possible :"
                           "`channel` (provide the id to reset a specific a channel instead of all the text channels)\n"
                           "`message_channel`\n"
                           "`reaction`\n"
                           "`server`")
            return

        await ctx.send(f"Statistics __{data}__ successfully reseted !")


    @commands.command(description = "Set the frequency you want to receive your server stats", aliases = ["set", "SET", "setstats"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def setStats(self, ctx, frequency = "daily"):
        """
        To choose the frequency of the stats delivery (used in the sendStat task look)
        The frequency is set to daily by default if no frequency given
        When the bot keyWord = server[0][7] # get the keyword of the server
        """

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
        """
        Stop the send of the stats for the server
        """

        self.DB.unsetSend(ctx.guild.id)
        await ctx.send("This channel will no longer receive your server stats !")


    @commands.command(description = "Erase the channel from the database", aliases = ["erasechannel", "erase_channel"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def eraseChannel(self, ctx, id : int):
        """
        A command to erase a channel from a database
        It will be automatically added if the autoAdd is set to enable
        The ID is needed to make sure that the user wants to erase it
        """

        if id is None:
            await ctx.send("You need to provide the channel id to make sure you want to delete it")
        
        elif id != ctx.channel.id:
            await ctx.send("The id needs to be equal to this current channel !")

        else:
            self.DB.deleteChannel(id)


    @commands.command(description = "Hide the channel to me", aliases = ["HIDE"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def hide(self, ctx):
        """
        Hide the channel to the bot
        If it has administrator permissions the command will be useless
        When the bot can't read messages from a channel, the on_message event is not triggered
        """
        
        if ctx.me.guild_permissions.administrator:
            await ctx.send("I have administator permissions, if i keep them this command is useless")
            return

        await ctx.channel.set_permissions(target = self.bot.user, read_messages = False,
                                                                  send_messages = False)


    @commands.command(description = "Turn on/off the auto refresh of the stats after the regular stats send (default ON)",
                      aliases = ["autorefresh", "auto_refresh"])
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    async def autoRefresh(self, ctx):
        """
        To disable or enable the refresh of the stats when serverStats command is triggered
        """

        new = ""
        status = ""

        # Get the status of the autoRefresh, 0 for disabled, 1 for enabled
        if self.DB.getGuild(ctx.guild.id)[0][10] == "0":
            new = "1"
            status = "auto refresh set to ON"
        else:
            new = "0"
            status = "auto refresh set to OFF" 

        """TODO : Enregistrer le nouveau statut"""
        await ctx.send(status)
            
    @commands.command(description = "",
                      aliases = [])
    @commands.has_permissions(administrator = True)
    @commands.guild_only()
    async def refresh(self, ctx):
        """
        A command to refresh the server stats (like the auto-refresh triggered in serverStats command)
        """

        self.DB.updStat(ctx.guild.id)
        self.DB.commitQ()
        await ctx.send("Server stats refreshed :ok_hand:")


    @commands.command(description = "Add the specified channel in the database", aliases = ["add_channel", "add_chan"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels = True)
    async def addChannel(self, ctx):
        """
        TODO : Create this command
        """
        pass


def setup(bot):
    """
    bot parameter pass to provide it to the class

    A function to load the extension
    automatically launched when the load or reload_extension methods are used
    """
    bot.add_cog(Admin(bot))