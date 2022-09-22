import discord
from discord.ext import commands
from discord import RawReactionActionEvent

from database.database import DatabaseHandler

class Events(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()

    async def updateRole(self, payload : RawReactionActionEvent):
        emoji = payload.emoji
        if emoji.is_custom_emoji():
            return

        msgId = payload.message_id
        resMsg = self.db.getMsg(msgId)
        if resMsg is None or len(resMsg) == 0:
            return

        if payload.message_id in resMsg:
            userId = payload.user_id
            guildId = payload.guild_id
            emojiName = emoji.name

            guild = self.bot.get_guild(guildId)
            member = guild.get_member(userId)

            resRoles = self.db.getRoleFromReact(msgId, emojiName)
            if resRoles is None:
                return

            roleId = resRoles[0]
            role = guild.get_role(roleId)

            if member.get_role(roleId):
                await member.remove_roles(role)
            else:
                await member.add_roles(role)
                

    @commands.Cog.listener()
    async def on_ready(self):
        print("\nUsing py-cord version", discord.__version__)
        print("\n----- J'aime les Stats ----- \n")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload : RawReactionActionEvent):
        await self.updateRole(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload : RawReactionActionEvent):
        await self.updateRole(payload)



def setup(bot : commands.Bot):
    bot.add_cog(Events(bot))