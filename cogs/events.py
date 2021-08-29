import discord
from discord.ext import commands
import datetime as dt

def setup(bot, cursor, cnx):
    bot.add_cog(Events(bot, cursor, cnx))

class Events(commands.Cog):
    def __init__(self, bot, cursor, cnx):
        self.bot = bot
        self.cursor = cursor
        self.cnx = cnx

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != self.bot.user:
            if not message.guild: 
                chan = self.bot.get_channel(737049189208555591)
                await chan.send(f"**{message.author.name}** : {message.content}")

        if not message.author.bot and message.guild:
            idAuth = message.author.id
            idChan = message.channel.id
            idGuild = message.guild.id

            getKW = f"SELECT keyWord FROM Guild WHERE idGuild = {idGuild};"
            self.cursor.execute(getKW)
            queryG = self.cursor.fetchall()

            if len(queryG) == 0:
                members = message.guild.members
                count = 0
                for member in members:
                    if not member.bot:
                        count += 1

                add_user = f"INSERT IGNORE User VALUES({member.id}, {member.created_at.year})"
                self.cursor.execute(add_user)

                add_guild = "INSERT INTO Guild(idGuild, totalMembers) VALUES(%s, %s);"
                data_guild = (idGuild, count)
                self.cursor.execute(add_guild, data_guild)

            elif queryG[0][0] != "":
                if queryG[0][0] in message.content.lower():
                    upd_kw = f"UPDATE Guild SET nbKeyWord = nbKeyWord + 1 WHERE idGuild = {idGuild};"
                    self.cursor.execute(upd_kw)

            upd_chan = f"UPDATE Channel SET numberMsg = numberMsg + 1 WHERE idChannel = {idChan};"
        
            select1 = f"SELECT idUser FROM User WHERE idUser = {idAuth};"
            self.cursor.execute(select1)
            query1 = self.cursor.fetchall()

            select2 = f"SELECT idUser FROM BelongC WHERE idUser = {idAuth} AND idChannel = {idChan};"
            self.cursor.execute(select2)
            query2 = self.cursor.fetchall()

            select3 = f"SELECT idUser FROM BelongG WHERE idUser = {idAuth} AND idGuild = {idGuild};"
            self.cursor.execute(select3)
            query3 = self.cursor.fetchall()
            
            if len(query1) == 0:
                add_member = "INSERT INTO User VALUES(%s, %s, NULL);"
                data_member = (idAuth, message.author.created_at.year)
                upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {message.guild.id};"

                self.cursor.execute(add_member, data_member)
                self.cursor.execute(upd_guild)

            if len(query2) == 0:
                self.cursor.execute("INSERT IGNORE Channel(idChannel, idGuild) VALUES(%s, %s);", (message.channel.id, message.guild.id))
                add_belongC = "INSERT INTO BelongC VALUES(%s, %s, 0);"
                data_belongC = (idAuth, idChan)
                self.cursor.execute(add_belongC, data_belongC)

            if len(query3) == 0:
                add_belongG = "INSERT INTO BelongG VALUES(%s, %s, 0, 0);"
                data_belongG = (idAuth, idGuild)
                self.cursor.execute(add_belongG, data_belongG)
            
            upd_belongC = f"UPDATE BelongC SET numberMsg = numberMsg + 1 WHERE idChannel = {idChan} AND idUser = {idAuth};"
            upd_belongG = f"UPDATE BelongG SET numberMsg = numberMsg + 1 WHERE idGuild = {message.guild.id} AND idUser = {idAuth};"

            self.cursor.execute(upd_chan)
            self.cursor.execute(upd_belongC)
            self.cursor.execute(upd_belongG)
            self.cnx.commit()


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        select = f"SELECT idGuild FROM Guild WHERE idGuild = {guild.id};"
        self.cursor.execute(select)
        if len(self.cursor.fetchall()) > 0:
            return

        members = guild.members
        count = 0
        for member in members:
            if not member.bot:
                count += 1

                add_user = f"INSERT IGNORE User VALUES({member.id}, {member.created_at.year})"
                self.cursor.execute(add_user)

        add_guild = "INSERT INTO Guild(idGuild, totalMembers) VALUES(%s, %s);"
        data_guild = (guild.id, count)
        self.cursor.execute(add_guild, data_guild)

        for chan in guild.text_channels:
            add_chan = "INSERT INTO Channel VALUES(%s, %s, %s);"
            data_chan = (chan.id, guild.id, 0)
            self.cursor.execute(add_chan, data_chan)

        for emoji in guild.emojis:
            add_emoji = "INSERT INTO Reaction VALUES(%s, %s, %s, %s);"
            data_emoji = (emoji.id, guild.id, 0, emoji.name)
            self.cursor.execute(add_emoji, data_emoji)

        updG = f"UPDATE Guild SET newMembers = newMembers + {count}, totalMembers = totalMembers + {count} WHERE idGuild = {guild.id};"
        self.cursor.execute(updG)
        self.cnx.commit()
        
        print(f"Added the guild {guild.name} to the database with \n• {count} members \n• {len(guild.text_channels)} text channels \n• {len(guild.emojis)} emojis")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del_belong = f"DELETE FROM BelongG WHERE idGuild = {guild.id};"
        del_chan = f"DELETE FROM Channel WHERE idGuild = {guild.id};"
        del_guild = f"DELETE FROM Guild WHERE idGuild = {guild.id};"

        self.cursor.execute(del_belong)
        self.cursor.execute(del_chan)
        self.cursor.execute(del_guild)
        self.cnx.commit()


    @commands.Cog.listener()
    async def on_member_join(self, member):
        if (member.bot):
            return
            
        update_join = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {member.guild.id};"
        self.cursor.execute(update_join)

        select = f"SELECT idUser FROM User WHERE idUser = {member.id};"
        self.cursor.execute(select)
        query = self.cursor.fetchall()

        if len(query) == 0:
            add_member = "INSERT INTO User VALUES(%s, %s, NULL);"
            data_member = (member.id, member.created_at.year)
            upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {member.guild.id};"

            self.cursor.execute(add_member, data_member)
            self.cursor.execute(upd_guild)

        add_belong = "INSERT INTO BelongG VALUES(%s, %s, 0, 0);"
        data_belong = (member.id, member.guild.id)
        self.cursor.execute(add_belong, data_belong)

        self.cnx.commit()


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if (member.bot):
            return

        update_rmv = f"UPDATE Guild SET lostMembers = lostMembers + 1, totalMembers = totalMembers - 1 WHERE idGuild = {member.guild.id};"
        self.cursor.execute(update_rmv)

        rmv_member = f"DELETE FROM BelongG WHERE idGuild = {member.guild.id} AND idUser = {member.id};"
        self.cursor.execute(rmv_member)
        self.cnx.commit()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        select = f"SELECT autoAdd FROM Guild WHERE idGuild = {channel.guild.id};"
        self.cursor.execute(select)
        query = self.cursor.fetchall()

        if query[0][0] == "1":
            add_channel = "INSERT INTO Channel VALUES(%s, %s, 0);"
            data_chan = (channel.id, channel.guild.id)
            self.cursor.execute(add_channel, data_chan)
            self.cnx.commit()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        del_belong = f"DELETE FROM BelongC WHERE idChannel = {channel.id};"
        del_channel = f"DELETE FROM Channel WHERE idChannel = {channel.id};"

        self.cursor.execute(del_belong)
        self.cursor.execute(del_channel)
        self.cnx.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id == None or payload.member.bot:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji():
            return

        select = f"SELECT idReact FROM Reaction WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
        self.cursor.execute(select)
        query = self.cursor.fetchall()

        if len(query) == 0:
            return

        upd_react = f"UPDATE Reaction SET numberReact = numberReact + 1 WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
        self.cursor.execute(upd_react)

        self.cnx.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id == None:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if len(guild.emojis) == 0 or payload.emoji.is_unicode_emoji():
            return

        select = f"SELECT idReact FROM Reaction WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
        self.cursor.execute(select)
        query = self.cursor.fetchall()

        if len(query) == 0:
            return

        upd_react = f"UPDATE Reaction SET numberReact = numberReact - 1 WHERE idGuild = {guild.id} AND idReact = {payload.emoji.id};"
        self.cursor.execute(upd_react)

        self.cnx.commit()

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        guild = self.bot.get_guild(message.guild.id)
        if len(guild.emojis) == 0:
            return

        for reaction in reactions:
            if not reaction.custom_emoji:
                return

            select = f"SELECT idReact FROM Reaction WHERE idGuild = {guild.id} AND idReact = {reaction.emoji.id};"
            self.cursor.execute(select)
            query = self.cursor.fetchall()

            if len(query) == 0:
                return

            upd_react = f"UPDATE Reaction SET numberReact = numberReact - {reaction.count} WHERE idGuild = {guild.id} AND idReact = {reaction.emoji.id};"
            self.cursor.execute(upd_react)

        self.cnx.commit()

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        select = f"SELECT idReact, nameReact FROM Reaction WHERE idGuild = {guild.id};"
        self.cursor.execute(select)
        query = self.cursor.fetchall()

        if len(before) < len(after):
            newEmoji = after[len(after) - 1]
            add_react = "INSERT INTO Reaction VALUES(%s, %s, %s, %s)"
            data_react = (newEmoji.id, guild.id, 0, newEmoji.name)
            self.cursor.execute(add_react, data_react)
            self.cnx.commit()
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
                    self.cursor.execute(del_react)
                    self.cnx.commit()
                    return

        else:
            for emoji in after:
                for row in query:
                    if row[0] == emoji.id:
                        if emoji.name != row[1]:
                            upd_react = f"UPDATE Reaction SET nameReact = '{emoji.name}' WHERE idReact = {emoji.id};"
                            self.cursor.execute(upd_react)
                            self.cnx.commit()
                            return

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        if before.channel == None:
            select = f"SELECT idUser FROM User WHERE idUser = {member.id};"
            self.cursor.execute(select)

            if len(self.cursor.fetchall()) == 0:
                add_user = "INSERT INTO User(idUser, yearDate) VALUES(%s, %s);"
                data_user = (member.id, member.created_at.year)
                add_belong = "INSERT INTO BelongG(idUser, idGuild) VALUES(%s, %s);"
                data_belong = (member.id, member.guild.id)
                upd_guild = f"UPDATE Guild SET newMembers = newMembers + 1, totalMembers = totalMembers + 1 WHERE idGuild = {member.guild.id};"

                self.cursor.execute(add_user, data_user)
                self.cursor.execute(add_belong, data_belong)
                self.cursor.execute(upd_guild)

            upd_user = f"UPDATE User SET joinVoc = NOW() WHERE idUser = {member.id};"
            self.cursor.execute(upd_user)

        elif after.channel == None:
            select = f"SELECT joinVoc FROM User WHERE idUser = {member.id};"
            self.cursor.execute(select)
            dateJoin = self.cursor.fetchall()[0][0]
            delta = (dt.datetime.now() - dateJoin).total_seconds()

            upd_user = f"UPDATE User SET joinVoc = NULL WHERE idUser = {member.id};"
            upd_belong = f"UPDATE BelongG SET nbSecond = nbSecond + {delta} WHERE idUser = {member.id} AND idGuild = {before.channel.guild.id};"
            self.cursor.execute(upd_user)
            self.cursor.execute(upd_belong)
        
        self.cnx.commit()


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
            await ctx.send("An error occured, it's because my dumb owner doesn't know how to code. \nSorry to bother you but could you report it to him ?")