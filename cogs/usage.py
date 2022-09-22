import discord
from discord.ext import commands
import random

from . import FILES

class Usage(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot

    @commands.command(description="The help command", aliases=["HELP"])
    async def help(self, ctx : commands.Context, commandName : str = None):
        if not commandName:
            helpEmbed = discord.Embed(title="Help embed", description=f"Use {self.bot.command_prefix}help [command_name] to see more info for a command", color = 0x0089FF)
            helpEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            helpEmbed.set_thumbnail(url=self.bot.user.avatar_url)
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
                        if command.hidden:
                            continue
                        lstCmd += "`" + command.name + "`, "
                    lstCmd = lstCmd[:len(lstCmd)-2]
                helpEmbed.add_field(name=cogName, value=lstCmd, inline=False)
            await ctx.send(embed=helpEmbed)

        else:
            commandName = commandName.lower()
            command = self.bot.get_command(commandName)
            if not command:
                await ctx.send(f":x: Unknown command, see {self.bot.command_prefix}help :x:")
                return   

            if len(command.aliases) == 0:
                al = "No aliases"
            else:
                al = ", ".join(command.aliases)

            if command.description == "":
                desc = "No description"
            else:
                desc = command.description

            usage = f"{self.bot.command_prefix}{command.name} "
            param = command.clean_params
            for val in param.values():
                default = val.default
                if str(default) != "<class 'inspect._empty'>": #Check if the parameter has a default value
                    if default == None:
                        default = ""
                    else:
                        default = f" = {default}"
                    usage += f"[{val.name}{default}] "

                else:
                    usage += f"<{val.name}> "

            embed2 = discord.Embed(title = "Help command", description = f"Description of the command **{command.name}**\n <> -> Forced parameters | [] -> Optional parameters", color = 0x0089FF)
            embed2.set_thumbnail(url = self.bot.user.avatar_url)
            embed2.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
            embed2.add_field(name = "Aliases :", value = al)
            embed2.add_field(name = "Description :", value = desc, inline = False)
            embed2.add_field(name = "Usage :", value = usage)
            await ctx.send(embed = embed2)
            

    @commands.command(description = "Give the latency of the bot", aliases = ["PING", "latency"])
    async def ping(self, ctx : commands.Context):
        await ctx.send(f"Pong ! Wait, you really think you can ping me and i will answer instantly... well you're right...\nI have a latency of {round((self.bot.latency * 1000), 2)} ms")
        await ctx.send(f"{ctx.author.mention} ||Just a revenge||")

    @commands.command(description="Randomly choose a sentence from a list", aliases=["CHOOSE"])
    async def choose(self, ctx : commands.Context, *, sentences : str):
        values = sentences.split(";")
        embed = discord.Embed(title="Result", description=random.choice(values))
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

def setup(bot : commands.Bot):
    bot.add_cog(Usage(bot))
