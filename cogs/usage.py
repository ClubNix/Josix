import discord
from discord.ext import commands
from discord import ApplicationContext
from discord import option

import random

from . import FILES


class Usage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        description="Get the help menu",
        options=[discord.Option(input_type=str,
            name="command_name",
            description="Name of the command",
            default=None,
        )]
    )
    async def help(self, ctx: ApplicationContext, command_name: str):
        av_aut = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar
        av_bot = self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar

        if not command_name:
            helpEmbed = discord.Embed(title="Help embed", description=f"Use /help [command_name] to see more info for a command", color = 0x0089FF)
            helpEmbed.set_author(name=ctx.author, icon_url=av_aut)
            helpEmbed.set_thumbnail(url=av_bot)
            for cogName in FILES:
                lstCmd = ""
                cog = self.bot.get_cog(FILES[cogName])

                if not cog:
                    continue
                commands = cog.get_commands()
                if len(commands) == 0:
                    lstCmd = "No commands available"
                else:
                    for command in commands:
                        lstCmd += "`" + command.qualified_name + "`, "
                    lstCmd = lstCmd[:len(lstCmd)-2]
                helpEmbed.add_field(name=cogName, value=lstCmd, inline=False)
            await ctx.respond(embed=helpEmbed)

        else:
            command_name = command_name.lower()
            command: discord.SlashCommand = self.bot.get_application_command(name=command_name, type=discord.SlashCommand)

            if not command:
                await ctx.respond(f":x: Unknown command, see /help :x:")
                return

            if command.description == "":
                desc = "No description"
            else:
                desc = command.description

            usage = f"/{command.name} "
            param = command.options
            options = ""
            
            for val in param:
                default = val.default
                if default:
                    default = f" = {default}"
                else:
                    default = ""
                    
                if val.required:
                    usage += f"<{val.name}{default}> "
                else:
                    usage += f"[{val.name}{default}] "

                options += f"**{val.name}** : {val.description}\n"
                    

            embed2 = discord.Embed(title = "Help command", description = f"Description of the command **{command.name}**\n <> -> Required parameters | [] -> Optional parameters", color = 0x0089FF)
            embed2.set_thumbnail(url = av_bot)
            embed2.set_author(name = ctx.author, icon_url = av_aut)
            embed2.add_field(name = "Description :", value = desc)
            embed2.add_field(name = "Usage :", value = usage, inline = False)
            embed2.add_field(name = "Options : ", value = options, inline = False)
            await ctx.respond(embed = embed2)

    @commands.slash_command(
        description="Randomly choose a sentence from a list",
        options=[discord.Option(input_type=str,
            name="sentences",
            description="List of sentences separated by a `;`",
            required=True
        )]
    )
    async def choose(self, ctx: ApplicationContext, sentences: str):
        values = sentences.split(";")
        embed = discord.Embed(title="Result", description=random.choice(values))
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Close a thread in the forum channel. Can only be used by the creator of the thread or a moderator")
    @option(
        name="lock",
        description="Lock the thread (moderator only)",
        type=bool,
        default=False
    )
    async def close(self, ctx: ApplicationContext, lock: bool):
        thread = ctx.channel
        if not (isinstance(thread, discord.Thread) and isinstance(thread.parent, discord.ForumChannel)):
            await ctx.respond("You can only close a thread created in the forum")
            return
    
        testMod = ctx.author.guild_permissions >= discord.Permissions(17179869184)
        if (ctx.author != thread.owner and not testMod) or (lock and not testMod): 
            await ctx.respond("You don't have the required permissions to do this")

        await ctx.respond(f"Closing the thread.\nLocking : {lock}")
        await thread.archive(locked=lock)
        

def setup(bot: commands.Bot):
    bot.add_cog(Usage(bot))
