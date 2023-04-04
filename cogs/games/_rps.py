import discord
from discord.ext import commands
from discord import ApplicationContext, Member, Interaction, option

from dataclasses import dataclass

class RPSButton(discord.ui.Button["RPSView"]):
    def __init__(self, gesture: str, index: int):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=RPSView.gestures[gesture])
        self.index = index
        self.gesture = gesture

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: RPSView = self.view

        user = interaction.user
        if not user:
            return

        p1, p2 = view.player1, view.player2
        data1, data2 = p1.playerData, p2.playerData

        if user.id != data1.id and user.id != data2.id:
            return

        if user.id == data1.id and view.player1.gestureVal != -1:
            return

        if user.id == data2.id and view.player1.gestureVal != -1:
            return

        if data1.id == user.id:
            view.player1.gestureVal = self.index
            view.player1.gestureName = self.gesture
        else:
            view.player2.gestureVal = self.index
            view.player2.gestureName = self.gesture

        if p1.gestureVal == -1 or p2.gestureVal == -1:
            await interaction.response.edit_message(embed=interaction.message.embeds[0], view=view)
            return

        result = view.checkWinner()
        if result == 0:
            desc = "It's a tie"
        else:
            winner, data = p1, data1 if result == 1 else p2, data2
            desc = f"{data.mention} won !"
            winner.nbWin += 1

        embed = discord.Embed(
            title=f"Rock-Paper-Scissord game : {data1.name} vs {data2.name}",
            description=desc,
            color=0x0089FF
        )
        embed.add_field(
            name=data1.mention,
            value=view.gestures.get(p1.gestureName)
        )
        embed.add_field(
            name=data2.mention,
            value=view.gestures.get(p2.gestureName)
        )
        embed.add_field(
            name="Results",
            value=f"{p1.nbWin} - {p2.nbWin}",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=view)
        view.clear()


class StopButton(discord.ui.Button["RPSView"]):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Stop")

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: RPSView = self.view

        user = interaction.user
        if not user:
            return

        data1 = view.player1.playerData
        data2 = view.player2.playerData

        if user.id != data1.id and user.id != data2.id:
            pass

        view.disable_all_items()
        embed = discord.Embed(
            title="Rock-Paper-Scissors game",
            description="Results",
            color=0x0089FF
        )
        embed.add_field(
            name=data1.name,
            value=view.player1.nbWin
        )
        embed.add_field(
            name=data2.name,
            value=view.player2.nbWin
        )
        await interaction.response.edit_message(embed=embed, view=view)

class RPSView(discord.ui.View):
    @dataclass
    class Player:
        """Class to represent a player"""
        playerData: Member
        nbWin: int = 0
        gestureVal: int = -1
        gestureName: str = ""

    children: list[RPSButton]
    gestures = {
        "rock":"🪨",
        "paper":"🍃",
        "scissors":"✂️"
    }

    def __init__(self, player1: Member, player2: Member) -> None:
        super().__init__()
        self.add_item(RPSButton("rock", 0))
        self.add_item(RPSButton("paper", 1))
        self.add_item(RPSButton("scissors", 2))
        self.add_item(StopButton())

        self.player1 = self.Player(player1)
        self.player2 = self.Player(player2)

    def checkWinner(self) -> int:
        condition = lambda x, y : (x - y) == 1 or (y == len(self.gestures) - 1 and x == 0)
        if condition(self.player1.gestureVal, self.player2.gestureVal):
            return 1
        else:
            if condition(self.player1.gestureVal, self.player2.gestureVal):
                return 2
            else:
                return 0

    def clear(self) -> None:
        self.player1.gestureName = ""
        self.player1.gestureVal = -1
        self.player2.gestureName = ""
        self.player2.gestureVal = -1
        

class RPS(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "games : rps"

    @commands.slash_command(description="Launch a game of rock-paper-scissors")
    @commands.guild_only()
    @option(
        input_type=Member,
        name="opponent",
        description="Your opponent",
        required=True
    )
    async def rock_paper_scissors(self, ctx: ApplicationContext, opponent: Member):
        view = RPSView(ctx.author, opponent)
        embed = discord.Embed(
            title=f"Rock Paper Scissors game",
            description=f"{view.player1.playerData.mention} VS {view.player2.playerData.mention}",
            color=0x0089FF
        )

        await ctx.respond(embed=embed, view=view)

def setup(bot: commands.Bot):
    bot.add_cog(RPS(bot))