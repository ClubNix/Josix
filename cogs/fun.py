import discord
from discord.ext import commands
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description = "If you want to know how slow I am and get an insult, use it !", aliases = ["PING"])
    async def ping(self, ctx):
        await ctx.send(f">Stupid ! You really think I am your slave {ctx.message.author.name} ?\n Btw I have a latency of {round(self.bot.latency*1000, 1)} ms") 

    @commands.command(description = "I repeat your sentence", aliases = ["SAY"])
    async def say(self, ctx, *txt):
        await ctx.send(" ".join(txt))
        await ctx.message.delete()

    @commands.command(description = "Send a random custom emote of the server", aliases = ["EMOTE", "emoji", "EMOJI"])
    @commands.guild_only()
    async def emote(self, ctx):
        lst = ctx.guild.emojis

        if len(lst) == 0:
            await ctx.send("Sorry, but it seems that your guild doesn't have any custom emotes")
        else:
            await ctx.send(random.choice(lst))

    @commands.command(description = "Everything is stonks", aliases = ["STONKS"])
    async def stonks(self, ctx):
        await ctx.send("https://cdn.radiofrance.fr/s3/cruiser-production/2021/04/b4f7bf1d-42da-44c2-b912-2b038635e102/801x410_main-qimg-14aa45f4a944de6acb372fa0d4e61a7a.jpg")
        await ctx.send(f"Stonks {ctx.author.mention} !")
        await ctx.message.delete()

    @commands.command(description = "I give you a nude in private", aliases = ["sendnude", "nude"])
    async def sendNude(self, ctx):
        await ctx.author.send("https://media0.giphy.com/media/PpNTwxZyJUFby/giphy.gif?cid=ecf05e4786byc2ho9urw2i4yf3rztiahjv31h0yx5z4qrklc&rid=giphy.gif&ct=g")
        await ctx.message.add_reaction("👀")

    @commands.command(description = "Use it to get your or someone avatar", aliases = ["AVATAR", "icon", "ICON"])
    async def avatar(self, ctx, user : discord.User = None):
        if user == None:
            await ctx.send(ctx.message.author.avatar_url)
        else:
            await ctx.send(user.avatar_url)

def setup(bot):
    bot.add_cog(Fun(bot))