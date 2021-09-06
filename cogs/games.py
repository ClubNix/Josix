import discord
from discord.ext import commands
import random
import os

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description = "Let's get a look at your luck by throwing some dices", aliases = ["ROLL"])
    async def roll(self, ctx, numberRolls : int = 1, mini : int = 1, maxi : int = 6):
        if mini < 0:
            mini = 1
        if maxi > 100:
            maxi = 6
        if mini > maxi:
            mini, maxi = 1, 6

        if numberRolls < 1 or numberRolls > 25:
            numberRolls = 1

        listRoll = []
        for _ in range(0, numberRolls):
            listRoll.append(random.randint(mini,maxi))
        total = sum(listRoll)
        moyenne = total / len(listRoll)

        embed = discord.Embed(title = f"{ctx.message.author.name}'s rolls :game_die:", color = 0x008000)
        embed.set_author(name = ctx.message.author, icon_url = ctx.message.author.avatar_url)
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/709732615980056606/858436523531567104/combien-de-joueurs-a-la-pC3A9tanque-pC3A9tanque-gC3A9nC3A9ration.png")
        embed.add_field(name = "Number of rolls :", value = f"**{numberRolls}**", inline = False)
        embed.add_field(name = "Rolls obtained :", value = f"{listRoll}", inline = False)
        embed.add_field(name = "Sum", value = f"{total}", inline = True)
        embed.add_field(name = "Average", value = f"{moyenne}", inline = True)
        await ctx.send(embed = embed)

    @commands.command(description = "Heads or Tails ?", aliases = ["FLIP"])
    async def flip(self, ctx):
        await ctx.send(f'> {random.choice(["Heads", "Tails"])}')

    @commands.command(description = "Draw a card", aliases = ["CARD", "draw", "DRAW"])
    async def card(self, ctx):
        cards = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J" , "Q", "K")
        colors = ("D", "S", "C", "H")
        card, color = random.choice(cards), random.choice(colors)
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, f'../deck/{card}{color}.png')
        file = discord.File(file_path, filename = "card.png")

        embed = discord.Embed(title = "Your card", description = "Here's the card you drew", color = 0x008000)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/709732615980056606/872917800551845918/cards.png")
        embed.set_footer(text = "Images from https://github.com/danwei002/Cards-Bot")
        embed.set_image(url = f"attachment://card.png")
        await ctx.send(file = file, embed = embed)

    @commands.command(description = "Play a game of roulette like you're at the casino !")
    async def roulette(self, ctx):
        colors = ("🟩", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "⬛", "🟥",
                  "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛",
                  "🟥", "⬛", "🟥", "⬛", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥", "⬛", "🟥"
        )
        column = ""
        dozen = ""
        color = ""

        number = random.randint(0, 36)
        color = colors[number]
        if number == 0:
            column = "No column"
        elif number % 3 == 1:
            column = "First column"
        elif number % 3 == 2:
            column = "Second column"
        else:
            column = "Third column"

        if number == 0:
            dozen = "No dozen"
        elif number < 13:
            dozen = "First dozen"
        elif number < 25:
            dozen = "Second dozen"
        else:
            dozen = "Third dozen"

        embed = discord.Embed(title = "Roulette time !", description = "Take your bet", color = 0x008000)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/709732615980056606/874040662587232267/220px-Roulette-finlandsfarja.png")
        embed.add_field(name = "Number :", value = number)
        embed.add_field(name = "Color :", value = color, inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "Column :", value = column, inline = True)
        embed.add_field(name = "Dozen :", value = dozen, inline = True)
        await ctx.send(embed = embed)

    @commands.command(description = "Do a game of Rock-Paper-Scissors against the bot !", aliases = ["RPS"])
    async def rps(self, ctx, gesture : str):
        moves = ["rock", "paper", "scissors"]
        emojis = [":rock:", ":leaves:", ":scissors:"]
        results = ["You won", "You lost", "It's a tie"]
        condition = lambda x, y : (x - y) == 1 or (y == len(moves) - 1 and x == 0)
        move = gesture.lower()
        botMove = random.randint(0, 2)
        userMove = 0
        winner = 0

        try:
            userMove = moves.index(move)
        except ValueError:
            await ctx.send("Move unavailable ! Choose `rock`, `paper` or `scissors`")
            return
    
        if condition(userMove, botMove):
            winner = 0
        else:
            if condition(botMove, userMove):
                winner = 1
            else:
                winner = 2

        embed = discord.Embed(title = "Rock Paper Scissors", description = "Result of the round", color = 0x008000)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/709732615980056606/884507061554147378/rockpaperscissors.png") 
        embed.add_field(name = "Result :", value = results[winner], inline = True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name= '\u200B', value= '\u200B', inline= True)
        embed.add_field(name = "User's move :", value = emojis[userMove], inline = True)
        embed.add_field(name = "Your move :", value = emojis[botMove])
        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(Games(bot))