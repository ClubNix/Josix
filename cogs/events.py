import discord
from discord.ext import commands

from database.database import DatabaseHandler

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseHandler()

    @commands.Cog.listener()
    async def on_ready(self):
        print("\n----- J'aime les Stats ----- \n")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        msgId = payload.message_id
        resMsg = self.db.getMsg(msgId)
        print(resMsg)

        return
        """
        Requête
        list = SELECT idMsg FROM MsgReact WHERE payload.guild_id == idGuild
        """
        if payload.message_id in []:
            userId = payload.user_id
            emojiId = payload.emoji
            """
            Requête
            id_role = SELECT idRole FROM MsgReact WHERE idReact==emojiId
            -> id_role à donner au user
            """
            id_role = 45
            if id_role in payload.guild_id.roles.id:
                await userId.add_roles(id_role)

            """
            Payload : channel_id, emoji, event_type, guild_id, member,
                message_id, user_id
            """


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Requête
        list = SELECT idMsg FROM MsgReact WHERE payload.guild_id == idGuild
        """
        if payload.message_id in []:
            userId = payload.user_id
            emojiId = payload.emoji
            """
            Requête
            id_role = SELECT idRole FROM MsgReact WHERE idReact==emojiId
            -> id_role à retirer au user
            """
            id_role = 45
            if id_role in payload.guild_id.roles.id:
                await userId.remove_roles(id_role)



def setup(bot):
    bot.add_cog(Events(bot))