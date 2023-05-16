import discord
from discord.ext import commands
from discord import ApplicationContext, option

import datetime

from enum import Enum
from dotenv import load_dotenv
from os import getenv
from urllib3 import disable_warnings
from requests import Session
from urllib3.exceptions import InsecureRequestWarning
from dataclasses import dataclass


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"


class MonixAPIError(Exception):
    """
    Exception for every Monix API errors
    """


class Monix(commands.Cog):
    @dataclass()
    class Element:
        """Class for an element"""
        name: str
        value: int
        isMember: bool

        def __str__(self) -> str:
            return f"• {self.name} (**{self.value}**" + (" coins)" if self.isMember else ")") + "\n"

    disable_warnings(InsecureRequestWarning)
    load_dotenv()
    _JOSIX_LOGIN = getenv("monix_log")
    _JOSIX_PSSWD = getenv("monix_psswd")
    _LOG_STOCK = getenv("home") + getenv("logs") + "stocks.txt"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.base_url = "https://monix.clubnix.fr/api"
        self.session = Session()
        self.session.verify = False
        self.generate_token()

    def generate_token(self) -> None:
        """
        Method to get the token of the bot and implements it in headers.
        Check if the token is valid with a basic call to the API
        """
        authentication = self.request(
            target="/auth/login",
            method=HTTPMethod.POST,
            json={
                "username": Monix._JOSIX_LOGIN,
                "password": Monix._JOSIX_PSSWD
            }
        )

        try:
            self.session.headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {authentication['data']['token']}"
            }
        except KeyError:
            raise MonixAPIError("Error on Josix login")

        try:
            checkToken = self.session.request(
                HTTPMethod.GET.value,
                self.base_url + "/users/1",
                json=None,
            )
            if checkToken.status_code == 403:
                raise MonixAPIError("Invalid token generated")
        except Exception:
            raise MonixAPIError("Unable to connect to the API")

    def request(
            self,
            target: str,
            method: HTTPMethod,
            json: str = None,
    ) -> dict:
        """
        Monix API function to create web requests originally created by Anemys.
        Args:
            target: The endpoint for accessing the ressources we aim for.
            params: dictionary of parameters for the function
        Returns
            A dictionary containing the function's results.
        """

        # Send the request
        try:
            data = self.session.request(
                method.value,
                self.base_url + target,
                json=json,
            )
        except Exception:
            raise MonixAPIError(f"Unable to connect to {self.base_url}")

        # Check that the API key wasn't rejected
        if data.status_code == 401:
            try:
                # Return the actual error message if the API returned valid JSON
                raise MonixAPIError(data.json()["error"])
            except Exception:
                raise MonixAPIError(data.text)
        elif data.status_code == 403:
            if str.lower(data.text["message"]).startswith("token"):
                self.generate_token()
                return self.request(target, method, json)
            else:
                raise MonixAPIError("Access Forbidden check credentials")
        elif data.status_code < 200 or data.status_code >= 300:
            raise MonixAPIError(f"Wrong status code obtained : {data.status_code}")

        # Parse the text into JSON
        try:
            data = data.json()
        except ValueError:
            raise MonixAPIError(f"Unable to parse JSON response : {data.text}")

        # Raise an exception if an error occurred
        if type(data) == dict and "error" in data:
            raise MonixAPIError(data["error"])

        # Return the data
        return data

    # -----------------------------
    #
    # Bot commands
    #
    # -----------------------------

    @commands.slash_command(description="Check the current stocks and ping the treasurer if they are low")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @option(
        input_type=bool,
        name="get_stocks",
        description="Get an output of all the stocks (in .txt file)",
        default=False
    )
    async def check_stocks(self, ctx: ApplicationContext, get_stocks: bool):
        await ctx.defer(ephemeral=False, invisible=False)
        if get_stocks and not ctx.author.guild_permissions.moderate_members:
            await ctx.respond("You don't have the required permissions to use this parameter")
            return

        data = self.request(
            target="/products/",
            method=HTTPMethod.GET
        )

        nbStocks = 0
        if get_stocks:
            with open(Monix._LOG_STOCK, "w") as f:
                for product in data["data"]:
                    nbStocks += product["stock"]
                    f.write(f"{product['name']} : {product['stock']}\n")
                f.write(f"\n===== Total : {nbStocks} =====\n")

        else:
            for product in data["data"]:
                nbStocks += product["stock"]

        if nbStocks < 50:
            roleT = ctx.guild.get_role(1017914272585629788)  # Role of the treasurer
            text = roleT.mention if roleT else "Role not found"

            lowEmbed = discord.Embed(
                title="Stocks",
                description=f"The stocks are low : **{nbStocks}** remaining\nYou better go shopping or the members "
                            f"will be hungry (and angry) !",
                color=0xFFCC00
            )
            lowEmbed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.respond(embed=lowEmbed)

        else:
            highEmbed = discord.Embed(
                title="Stocks",
                description=f"There is enough stocks : **{nbStocks}** remaining\nNo need to go shopping now !",
                color=0x1cb82b
            )
            highEmbed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
            await ctx.respond(embed=highEmbed)

    def compareTop(self, top: list[Element], recordVal: int) -> int:
        if len(top) >= 5:
            if top[4].value >= recordVal:
                return -1

            for index, elmt in enumerate(top):
                if recordVal > elmt.value:
                    return index

        else:
            for index, elmt in enumerate(top):
                if recordVal > elmt.value:
                    return index
            return len(top)

    def compareBottom(self, bottom: list[Element], recordVal: int) -> int:
        if len(bottom) >= 5:
            if bottom[4].value <= recordVal:
                return -1

            for index, elmt in enumerate(bottom):
                if recordVal < elmt.value:
                    return index

        else:
            for index, elmt in enumerate(bottom):
                if recordVal < elmt.value:
                    return index
            return len(bottom)

    @commands.slash_command(description="Leaderboard of the most and least rich members in Monix")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @option(
        input_type=int,
        name="value_type",
        description="Which leaderboard you want to see",
        required=True,
        choices=[
            discord.OptionChoice(name="Members", value=0),
            discord.OptionChoice(name="Products", value=1)
        ]
    )
    async def monix_leaderboard(self, ctx: ApplicationContext, value_type: int):
        await ctx.defer(ephemeral=False, invisible=False)
        if value_type != 0 and value_type != 1:
            await ctx.respond("Unknown value")
            return

        data = self.request(
            target="/users/" if value_type == 0 else "/products",
            method=HTTPMethod.GET
        )

        name_type = "members" if value_type == 0 else "products"
        name_record = "username" if value_type == 0 else "name"
        name_data = "balance" if value_type == 0 else "stock"
        top: list[Monix.Element] = []
        bottom: list[Monix.Element] = []

        for record in data["data"]:
            recordVal = record[name_data]
            recordName = record[name_record]

            if recordName is None or recordVal is None:
                continue

            if record["id"] == 1 and value_type == 0:
                continue

            newElmt = Monix.Element(record[name_record], recordVal, value_type == 0)
            checkT = self.compareTop(top, recordVal)
            if checkT > -1:
                top.insert(checkT, newElmt)
                if len(top) > 5:
                    top.pop()

            # We pass this part for products because a lot of products are at 0 and can't be less
            if value_type == 1:
                continue

            checkB = self.compareBottom(bottom, recordVal)
            if checkB > -1:
                bottom.insert(checkB, newElmt)
                if len(bottom) > 5:
                    bottom.pop()

        embed = discord.Embed(
            title="Leaderboard",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.add_field(name="Top " + name_type, value="".join(map(str, top)))

        if value_type == 0:
            embed.add_field(name="Bottom " + name_type, value="".join(map(str, bottom)))
        await ctx.respond(embed=embed)

    def getHistoryValues(self, isMember: bool) -> dict[int, Element]:
        data = self.request(
            "/history/",
            HTTPMethod.GET,
        )

        today = datetime.date.today()
        records = data['data']
        elements: dict[int, Monix.Element] = {}
        idUser = 0
        nameUser = ""
        valTransac = 0

        for record in records:
            dateRecord = datetime.datetime.strptime(record['date'].split("T")[0], "%Y-%m-%d").date()
            if (today - dateRecord).days > 7:
                break

            try:
                if isMember:
                    if record['User'] is None:
                        continue
                    idUser, nameUser, valTransac = record['User']['id'], record['User']['username'], record['movement']
                else:
                    if record['Product'] is None:
                        continue
                    idUser, nameUser = record['Product']['id'], record['Product']['name']
                    valTransac = int(-(record['movement'] / record['Product']['price']))

                # We want to look at how many credits a member lost or how many products have been sold
                if (isMember and valTransac >= 0) or (not isMember and valTransac <= 0):
                    continue

                elmt = elements.get(idUser)
                if elmt is None:
                    elements[idUser] = Monix.Element(nameUser, valTransac, isMember)
                else:
                    elements[idUser].value += valTransac
            except KeyError as e:
                continue

        return elements

    def sortElements(self, elements: list[Element], isMember: bool) -> list[Element]:
        n = len(elements)
        if n == 1:
            return elements

        arraySorted = False
        for i in range(n):
            arraySorted = True
            for j in range(n - 1 - i):
                if isMember:
                    if elements[j].value > elements[j + 1].value:
                        elements[j], elements[j + 1] = elements[j + 1], elements[j]
                        arraySorted = False
                else:
                    if elements[j].value < elements[j + 1].value:
                        elements[j], elements[j + 1] = elements[j + 1], elements[j]
                        arraySorted = False
            if arraySorted:
                break

        return elements

    @commands.slash_command(description="Ranking of the most consumed products during the last 7 days")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def products_ranking(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        elements = self.getHistoryValues(False)

        if len(elements.keys()) == 0:
            await ctx.respond("No transaction found during the last 7 days")
            return

        sortedElmts = self.sortElements(list(elements.values()), False)[:10]
        embed = discord.Embed(
            title="Monix Ranking",
            description="Biggest consumed products",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.add_field(name="Rank", value="".join(map(str, sortedElmts)))
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Ranking of the biggest consumers during the last 7 days")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def members_ranking(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=False, invisible=False)
        elements = self.getHistoryValues(True)

        if len(elements.keys()) == 0:
            await ctx.respond("No transaction found during the last 7 days")
            return

        sortedElmts = self.sortElements(list(elements.values()), True)[:10]
        embed = discord.Embed(
            title="Monix Ranking",
            description="Biggest monix consumers",
            color=0x0089FF
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar)
        embed.add_field(name="Rank", value="".join(map(str, sortedElmts)))
        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Monix(bot))
