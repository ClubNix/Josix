import discord
from discord.ext import commands
import datetime as dt
from database.database import DatabaseHandler

class Events(commands.Cog):
    """
    Cog for the events

    An extension that manage all the events for the bot.
    It's triggered when a messager is send, reaction added/removed/cleared, etc...
    """

    def __init__(self, bot):
        self.bot = bot
        self.DB = DatabaseHandler()

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        event on_message triggered when a message is sent (works in dm)

        - 1 : stop if the message has been send by a bot or not in a server
        - 2 : If the server is not in the database it's added and his users are loaded
        - 3 : Updates the count of use of keyword if present in the message
        - 4 : Check if the user, the channel is in the guild and the user is known in the channel
              if not, they each are added in the database 
        """

        if not message.author.bot and message.guild: #1
            idAuth = message.author.id
            idChan = message.channel.id
            idGuild = message.guild.id

            server = self.DB.getGuild(idGuild) # get the informations of the server 
            keyWord = server[0][7] # get the keyword of the server

            if len(server) == 0: #2
                members = message.guild.members
                count = 0
                for member in members:
                    if not member.bot:
                        count += 1
                        if len(self.DB.getUser(member.id)) > 0:
                            self.DB.newUser(member.id, idGuild, member.created_at.year, False)
                self.DB.addGuild(idGuild, count)

            elif not keyWord or keyWord != "": #3
                if keyWord in message.content.lower():
                    self.DB.updCountKW(idGuild, 1)

            # 4
            user = self.DB.getUser(idAuth)
            userBG = self.DB.getBG(idAuth, 2, idGuild) # check if the user is in the guild
            channelBC = self.DB.getBC(idAuth, 2, idChan) # check if the user is registered in the channel
            
            if len(user) == 0:
                self.DB.addOneUser(idAuth, idGuild, message.author.created_at.year)

            if len(channelBC) == 0:
                self.DB.addChannel(idChan, idGuild, False)
                self.DB.addBC(idAuth, idChan, False)

            if len(userBG) == 0:
                self.DB.addBG(idAuth, idGuild, False)
            
            self.DB.addMsg(idAuth, idGuild, idChan) # Then add the message stats in the database


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        An event triggered when the bot join a server 

        - 1 : check if the server was already in the database (bot kicked when offline)
        - 2 : Load the users in the database
        - 3 : Load the channels (where the bot can read) in the database 
        - 4 : Load the emojis in the database (only custom emojis)
        """

        idGuild = guild.id
        #1
        if len(self.DB.getGuild(idGuild)) > 0:
            return

        #2
        members = guild.members
        count = 0
        for member in members:
            if not member.bot:
                count += 1
                if len(self.DB.getUser(idGuild)) > 0:
                    self.DB.newUser(member.id, idGuild, member.created_at.year, False)
        self.DB.addGuild(idGuild, count)

        #3
        me = guild.get_member(713164137194061916)
        for chan in guild.text_channels:
            if chan.permissions_for(me).read_messages: # Check if the bot can read the messages in the channel
                self.DB.addChannel(chan.id, idGuild, False)

        #4
        for emoji in guild.emojis:
            self.DB.addReact(emoji.id, idGuild, emoji.name, False)

        self.DB.updNewMembers(count, idGuild) # Update the member count
        print(f"Added the guild {guild.name} to the database with \n• {count} members \n• {len(guild.text_channels)} text channels \n• {len(guild.emojis)} emojis")


    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """
        An event triggered when the bot is kicked/banned from the server, or if it's deleted
        """

        # If the server is in the database then it's removed
        if len(self.DB.getGuild(guild.id)) == 0:
            return
        self.DB.deleteGuild(guild.id)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        An event triggered when a member join the server
        """

        if (member.bot): # Do northing if it's a bot
            return

        idGuild = member.guild.id
        idUser = member.id

        # If the server not in the databse, then it's added
        if len(self.DB.getGuild(idGuild)) == 0:
            self.addGuild(idGuild, False)

        # If the user not in the database the bot is add it
        if len(self.DB.getUser(idUser)) == 0:
            self.DB.addOneUser(idUser, idGuild, member.created_at.year)

        # If the user and the server are not linked then... it links them
        if len(self.DB.getBG(member.id, 2, member.guild.id)) == 0:
            self.DB.addBG(idUser, idGuild, True)


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        An event triggered when a member is kicked/banned of the server
        """

        if (member.bot):
            return

        # If the user not in the database then there's nothing to do
        if len(self.DB.getUser(member.id)) == 0:
            return

        self.DB.rmvMember(member.id, member.guild.id)
        if len(self.DB.getBG(member.id, 0)) == 0:
            self.DB.deleteUser(member.id)


    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """
        An event triggered when a channel is created
        """


        if self.DB.getGuild(channel.guild.id)[0][9] == "0": #Check if the auto-add is enable
            return
        self.DB.addChannel(channel.id, channel.guild.id, True)


    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """
        An event triggered when a channel is deleted
        """
        self.DB.deleteChannel(channel.id)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        An event triggered when a reaction add
        we use 'raw' because the "on_reaction_add" is triggered only with message present in bot cache
        """

        if payload.guild_id == None or payload.member.bot:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji(): # check if it's an emoji by default
            return

        idEmoji = payload.emoji.id
        if len(self.DB.getReact(idEmoji)) == 0:
            return

        self.DB.newReact(idEmoji)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        An event triggered when a reaction is remove
        we use 'raw' because the "on_reaction_remove" is triggered only with message present in bot cache
        """

        if payload.guild_id == None:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji(): # check if it's an emoji by default
            return

        if len(self.DB.getReact(payload.emoji.id)) == 0:
            return

        self.DB.reactRemove(payload.emoji.id, 1)


    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        """
        An event triggered when the reactions are cleared 
        Doesn't work if the message is not in the cache
        """

        guild = self.bot.get_guild(message.guild.id)
        if len(guild.emojis) == 0:
            return

        for reaction in reactions:
            # Pass if the emoji if it's not a custom one or not in the server
            if not reaction.custom_emoji or len(self.DB.getReact(reaction.emoji.id)) == 0:
                continue

            self.DB.reactRemove(reaction.emoji.id, reaction.count)
        
            
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """
        an event triggered when an emoji is added/removed/renamed
        before is a list of the emojis before the update
        after is a list of the emojis after the update
        """

        query = self.DB.getReactGuild(guild.id) # All the emojis of the server

        # if the after is bigger than the before that means an emoji has been added
        if len(before) < len(after):
            # A new emoji is at the end of the list
            newEmoji = after[len(after) - 1]
            self.DB.addReact(newEmoji.id, guild.id, newEmoji.name, True)
            return

        # Here it means an emoji has been removed
        elif len(before) > len(after):
            for row in query:
                isPresent = False
                for emoji in after:
                    # Check which emoji has been removed
                    if row[0] == emoji.id:
                        isPresent = True
                        break

                if not isPresent:
                    self.DB.deleteReact(row[0])
                    return

        # If an emoji has been updated 
        else:
            for emoji in after:
                for row in query:
                    if row[0] == emoji.id:
                        if emoji.name != row[3]:
                            self.DB.newReactName(row[0], emoji.name)
                            return


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        An event triggered when a voice_channel activity has been updated 
        The member represents the member at the origin of the update (muted, etc...)
        """

        if member.bot:
            return

        # If there's no before, the member just joined the voice chat
        # Add the user in the DB if not in then register the date when he joined the VC
        if before.channel == None:
            if len(self.DB.getUser(member.id)) == 0:
                self.DB.addOneUser(member.id, member.guild.id, member.created_at.year)
            self.DB.setJoinVoc(member.id)

        # If there's no after, the member just left the voice chat
        # Check if the bot registered the member join
        elif after.channel == None:
            join = self.DB.getUser(member.id)[0][2]
            if join != None:
                # Calculate the time passed in VC then reset his the join date and add the delta
                delta = (dt.datetime.now() - join).total_seconds()
                self.DB.resetJoin(member.id, before.channel.guild.id, delta)


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        An event triggered when an error is launched by a command 
        """

        if isinstance(error, commands.MissingPermissions): # User doesn't have the required permissions to use the command
            await ctx.send("Sorry, you don't have the required permissions")

        elif isinstance(error, commands.MissingRequiredArgument): # User didn't pass the required arguments
            await ctx.send("This command requires one or several arguments")

        elif isinstance(error, discord.Forbidden): # Can't send dm 
            await ctx.send("I can't send the message, if it's for the nude, it's private so let me talk to you !")

        elif isinstance(error, commands.CommandNotFound): # Unknown command passed
            await ctx.send("This command doesn't exist")

        elif isinstance(error, commands.CommandOnCooldown): # Command on cooldown
            await ctx.send("You still on a cooldown for this command, please wait")

        elif isinstance(error, commands.DisabledCommand): # Command disabled
            await ctx.send("This command is disabled")

        else:
            # If it's not an error from discord, print the error
            print(error)
            await ctx.send("Something went wrong")

def setup(bot):
    bot.add_cog(Events(bot))