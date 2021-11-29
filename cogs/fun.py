import discord
from discord.ext import commands
import random

class Fun(commands.Cog):
    """
    A cog to manage the fun commands of the bot

    This extension regroups all the commands that are used to be fun
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description = "If you want to know how slow I am and get an insult, use it !", aliases = ["PING"])
    async def ping(self, ctx):
        """
        get the ping of the bot in milliseconds
        """
        await ctx.send(f">Stupid ! You really think I am your slave {ctx.message.author.name} ?\n Btw I have a latency of {round(self.bot.latency*1000, 1)} ms") 

    @commands.command(description = "I repeat your sentence", aliases = ["SAY"])
    async def say(self, ctx, *txt):
        """
        The bot will repeat the message given in parameter
        """
        await ctx.send(" ".join(txt))
        await ctx.message.delete()

    @commands.command(description = "Send a random custom emote of the server", aliases = ["EMOTE", "emoji", "EMOJI"])
    @commands.guild_only()
    async def emote(self, ctx):
        """
        Get an random emote from the list of custom emotes in the server
        """

        lst = ctx.guild.emojis
        if len(lst) == 0:
            await ctx.send("Sorry, but it seems that your guild doesn't have any custom emotes")
        else:
            await ctx.send(random.choice(lst))

    @commands.command(description = "Use it to get your or someone avatar", aliases = ["AVATAR", "icon", "ICON"])
    async def avatar(self, ctx, user : discord.User = None):
        """
        Get the avatar of the mentioned user
        If no user have been mentioned, it gives the author's avatar
        """
        if user == None:
            await ctx.send(ctx.message.author.avatar_url)
        else:
            await ctx.send(user.avatar_url)

def setup(bot):
    bot.add_cog(Fun(bot))