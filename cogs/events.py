import discord
from discord.ext import commands
import datetime as dt
from database.database import DatabaseHandler

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB = DatabaseHandler()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild: 
            if message.author != self.bot.user:
                chan = self.bot.get_channel(737049189208555591)
                await chan.send(f"**{message.author.name}** : {message.content}")

        if not message.author.bot and message.guild:
            idAuth = message.author.id
            idChan = message.channel.id
            idGuild = message.guild.id

            server = self.DB.getGuild(idGuild)
            keyWord = server[0][7]

            if len(server) == 0:
                members = message.guild.members
                count = 0
                for member in members:
                    if not member.bot:
                        count += 1
                        if len(self.DB.getUser(member.id)) > 0:
                            self.DB.newUser(member.id, idGuild, member.created_at.year, False)
                self.DB.addGuild(idGuild, count)

            elif not keyWord or keyWord != "":
                if keyWord in message.content.lower():
                    self.DB.updCountKW(idGuild, 1)

            user = self.DB.getUser(idAuth)
            userBG = self.DB.getBG(idAuth, 2, idGuild)
            channelBC = self.DB.getBC(idAuth, 2, idChan)
            
            if len(user) == 0:
                self.DB.addOneUser(idAuth, idGuild, message.author.created_at.year)

            if len(channelBC) == 0:
                self.DB.addChannel(idChan, idGuild, False)
                self.DB.addBC(idAuth, idChan, False)

            if len(userBG) == 0:
                self.DB.addBG(idAuth, idGuild, False)
            
            self.DB.addMsg(idAuth, idGuild, idChan)


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        idGuild = guild.id

        if len(self.DB.getGuild(idGuild)) > 0:
            return

        members = guild.members
        count = 0
        for member in members:
            if not member.bot:
                count += 1
                if len(self.DB.getUser(idGuild)) > 0:
                    self.DB.newUser(member.id, idGuild, member.created_at.year, False)
        self.DB.addGuild(idGuild, count)

        me = guild.get_member(713164137194061916)
        for chan in guild.text_channels:
            if chan.permissions_for(me).read_messages:
                self.DB.addChannel(chan.id, idGuild, False)

        for emoji in guild.emojis:
            self.DB.addReact(emoji.id, idGuild, emoji.name, False)

        self.DB.updNewMembers(count, idGuild)
        print(f"Added the guild {guild.name} to the database with \n• {count} members \n• {len(guild.text_channels)} text channels \n• {len(guild.emojis)} emojis")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if len(self.DB.getGuild(guild.id)) == 0:
            return
        self.DB.deleteGuild(guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if (member.bot):
            return

        idGuild = member.guild.id
        idUser = member.id

        if len(self.DB.getGuild(idGuild)) == 0:
            self.addGuild(idGuild, False)

        if len(self.DB.getUser(idUser)) == 0:
            self.DB.addOneUser(idUser, idGuild, member.created_at.year)

        if len(self.DB.getBG(member.id, 2, member.guild.id)) == 0:
            self.DB.addBG(idUser, idGuild, True)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if (member.bot):
            return

        if len(self.DB.getUser(member.id)) == 0:
            return
        self.DB.rmvMember(member.id, member.guild.id)

        if len(self.DB.getBG(member.id, 0)) == 0:
            self.DB.deleteUser(member.id)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if self.DB.getGuild(channel.guild.id)[0][9] == "0":
            return
        self.DB.addChannel(channel.id, channel.guild.id, True)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        self.DB.deleteChannel(channel.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id == None or payload.member.bot:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji():
            return

        idEmoji = payload.emoji.id
        if len(self.DB.getReact(idEmoji)) == 0:
            return

        self.DB.newReact(idEmoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id == None:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji():
            return

        if len(self.DB.getReact(payload.emoji.id)) == 0:
            return

        self.DB.reactRemove(payload.emoji.id, 1)

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        guild = self.bot.get_guild(message.guild.id)
        if len(guild.emojis) == 0:
            return

        for reaction in reactions:
            if not reaction.custom_emoji or len(self.DB.getReact(reaction.emoji.id)) == 0:
                return

            self.DB.reactRemove(reaction.emoji.id, reaction.count)
            
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        query = self.DB.getReactGuild(guild.id)

        if len(before) < len(after):
            newEmoji = after[len(after) - 1]
            self.DB.addReact(newEmoji.id, guild.id, newEmoji.name, True)
            return

        elif len(before) > len(after):
            for row in query:
                isPresent = False
                for emoji in after:
                    if row[0] == emoji.id:
                        isPresent = True
                        break

                if not isPresent:
                    self.DB.deleteReact(row[0])
                    return

        else:
            for emoji in after:
                for row in query:
                    if row[0] == emoji.id:
                        if emoji.name != row[3]:
                            self.DB.newReactName(row[0], emoji.name)
                            return

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if before.channel == None:
            if len(self.DB.getUser(member.id)) == 0:
                self.DB.addOneUser(member.id, member.guild.id, member.created_at.year)
            self.DB.setJoinVoc(member.id)

        elif after.channel == None:
            join = self.DB.getUser(member.id)[0][2]
            if join != None:
                delta = (dt.datetime.now() - join).total_seconds()
                self.DB.resetJoin(member.id, before.channel.guild.id, delta)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
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
            await ctx.send("Something went wrong")

def setup(bot):
    bot.add_cog(Events(bot))