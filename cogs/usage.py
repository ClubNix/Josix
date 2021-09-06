import discord
from discord.ext import commands
import cogs.__init__ as init
from database.database import DatabaseHandler

class Usage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB = DatabaseHandler()

    @commands.command(description = "Help command of the bot", aliases = ["HELP"])
    async def help(self, ctx, commandName = None):
        if commandName == None:
            embed = discord.Embed(title = "Help command", description = f"Description of the commands, use `{self.bot.command_prefix}help [commandName]` to get more info about a specific command", color = 0x0089FF)
            embed.set_thumbnail(url = self.bot.user.avatar_url)
            embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
            for cogName in init.names:
                lst = ""
                className = init.names[cogName]
                cog = self.bot.get_cog(className)
                for command in cog.get_commands():
                    lst += "`" + command.name + "`, "
                if cogName != "events":
                    embed.add_field(name = className + " commands", value = lst[:len(lst) - 2], inline = False)
            embed.add_field(name = "Other informations :", value = f"""• Owner : {self.bot.get_user(237657579692621824)} \n• prefix : `{self.bot.command_prefix}`\n• Invite the bot : `{self.bot.command_prefix}invite` \n• More informations : `{self.bot.command_prefix}info`""")
            await ctx.send(embed = embed)

        else:
            cmd = self.bot.get_command(commandName)
            if cmd == None or cmd.hidden:
                await ctx.send("Unknown command :x:")
                return

            if len(cmd.aliases) == 0:
                al = "No aliases"
            else:
                al = ", ".join(cmd.aliases)

            if cmd.description == "":
                desc = "No description"
            else:
                desc = cmd.description

            usage = f"{self.bot.command_prefix}{cmd.name} "
            param = cmd.clean_params
            for val in param.values():
                default = val.default
                if str(default) != "<class 'inspect._empty'>":
                    if default == None:
                        default = ""
                    else:
                        default = f" = {default}"
                    usage += f"[{val.name}{default}] "

                else:
                    usage += f"<{val.name}> "

            embed2 = discord.Embed(title = "Help command", description = f"Description of the command **{cmd.name}**\n <> -> Forced parameters | [] -> Optional parameters", color = 0x0089FF)
            embed2.set_thumbnail(url = self.bot.user.avatar_url)
            embed2.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
            embed2.add_field(name = "Aliases :", value = al)
            embed2.add_field(name = "Description :", value = desc, inline = False)
            embed2.add_field(name = "Usage :", value = usage)
            await ctx.send(embed = embed2)

    @commands.command(description = "Important informations about the bot", aliases = ["INFO", "informations", "INFORMATIONS"])
    async def info(self, ctx):
        embed = discord.Embed(title = "Important informations", description = "Read this to be aware of how I work", color = 0x0089FF)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = self.bot.user.avatar_url)
        embed.add_field(name = "What I do ?",
                        value = "I register data about the members of the server and the server itself to show you some statistics. You can also use me for some fun commands and games of luck !",
                        inline = False)
        embed.add_field(name = "Channel activity",
                        value = "Be careful, I monitor when you create a channel and I add it to my database (see the `autoAdd` command) but if I can't read the messages I will not be able to update my data in this channel !",
                        inline = False)
        embed.add_field(name = "Kick, ban etc...",
                        value = "If a member is kicked or banned from the server I will instantly remove all his data from my database so be aware of that. Same thing if I leave the server, I will clean this part of my memory !",
                        inline = False)
        embed.add_field(name = "Disconnections",
                        value = "I can disconnect sometimes, remember to run the `load` commands to be sure that the server data is up-to-date !",
                        inline = False)
        embed.add_field(name = "Help me 😭 :",
                        value = "English is not the native language of my creator, if you find some errors in the sentences etc... report them ! \nSame thing if you find errors in the commands or get some ideas, it helps a lot !",
                        inline = False)
        await ctx.send(embed = embed)

    @commands.command(description = "Get the link to invite the bot", aliases = ["INVITE", "link", "LINK"])
    async def invite(self, ctx):
        await ctx.send("There's no link currently ¯\_(ツ)_/¯")

    @commands.command(description = "To get the bio of my creator", aliases = ["BIO"])
    async def bio(self, ctx):
        await ctx.send("https://dsc.bio/hitsuji")

    @commands.command(description = "Some informations about me", aliases = ["ME", "bot", "BOT", "bot_info"])
    async def me(self, ctx):
        me = self.bot.get_user(237657579692621824)
        usersCount = self.DB.countUser()
        guildsCount = self.DB.countGuild()

        embed = discord.Embed(title = "Random data command", description = "Just some useless data", color = 0x0089FF)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.add_field(name = "Creation date", value = self.bot.user.created_at.strftime("%D"))
        embed.add_field(name = "Developed with", value = f"Discord.py version {discord.__version__}")
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "My creator", value = me)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "Total of users", value = usersCount)
        embed.add_field(name = "Number of servers", value = guildsCount)
        embed.add_field(name = "Number of commands", value = len(self.bot.commands))
        embed.set_footer(text = "I hope you have fun with my (useless) bot ^^")

        await ctx.send(embed = embed)

    @commands.command(description = "Delete all your data from the database", aliases = ["DELETE"])
    async def delete(self, ctx, user : discord.User = None):
        if not user:
            await ctx.send("This command will delete all your data (and erase you from the database) ! To perform it you have to mention yourself !")
            return

        elif (ctx.author == user) or (ctx.author.id == self.bot.owner_id):
            self.DB.deleteUser(ctx.author.id)

        else:
            await ctx.send("You can't delete another user data !")
            return

def setup(bot):
    bot.add_cog(Usage(bot))