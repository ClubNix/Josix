import discord
from discord.ext import commands
from discord.ext.commands import BotMissingPermissions, MissingPermissions, MissingRequiredArgument, NoPrivateMessage, CommandOnCooldown
from discord import RawReactionActionEvent, ApplicationContext, DiscordException
from discord import Forbidden, NotFound

from database.database import DatabaseHandler

import logwrite as log

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseHandler()

    async def updateRole(self, payload: RawReactionActionEvent, add: bool):
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

            if add:
                if not member.get_role(roleId):
                    await member.add_roles(role)
            else:
                if member.get_role(roleId):
                    await member.remove_roles(role)


##### ================================================== #####
##### ================================================== #####
##### ================================================== #####


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        await self.updateRole(payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        await self.updateRole(payload, False)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if not isinstance(thread.parent, discord.ForumChannel):
            return
        await thread.send("This thread is now open. You can close it automatically by using `/close`")

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: ApplicationContext, error: DiscordException):
        if isinstance(error, Forbidden):
            await ctx.respond("Ho no i can't do something :(")
        elif isinstance(error, NotFound):
            await ctx.respond("Bip Boup **Error 404**")
        elif isinstance(error, BotMissingPermissions):
            await ctx.respond("HEY ! Gimme more permissions...")
        elif isinstance(error, MissingPermissions):
            await ctx.respond("Sorry but you lack permissions (skill issue)")
        elif isinstance(error, MissingRequiredArgument):
            await ctx.respond("An argument is missing in your command (skill issue n°2)")
        elif isinstance(error, NoPrivateMessage):
            await ctx.respond("This command can only be used in a server (get some friends)")
        elif isinstance(error, CommandOnCooldown):
            error : CommandOnCooldown = error
            await ctx.respond(f"Too fast bro, wait {round(error.retry_after, 2)} seconds to retry this command")
        else:
            await ctx.respond("Unknown error occured")
            log.writeError(str(error))
        

def setup(bot: commands.Bot):
    bot.add_cog(Events(bot))