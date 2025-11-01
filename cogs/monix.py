import datetime
from dataclasses import dataclass
from enum import Enum
from os import getenv

import discord
from discord import ApplicationContext, option
from discord.ext import commands
from dotenv import load_dotenv
from requests import Session  # type: ignore
from urllib3 import disable_warnings  # type: ignore
from urllib3.exceptions import InsecureRequestWarning  # type: ignore

from josix import Josix
from pkg.bot_utils import JosixCog, josix_slash

DISABLE_MONIX = True

class HTTPMethod(Enum):
    """Enumerator that represents HTTP method used for the bot"""
    GET = "GET"
    POST = "POST"


class MonixAPIError(Exception):
    """Exception for every Monix API errors"""


class Monix(JosixCog):
    """
    Represents the Monix extension of the bot

    Attributes
    ----------
    bot : Josix
        The bot that loaded this extension
    base_url : str
        The url of the Monix API
    session : Session
        The session for every request to the API

    Methods
    -------
    generate_token():
        Generate the token for the session with the given username and password

    request(target: str, method: HTTPMethod, json: str = None):
        Execute a request to the target endpoint of the API and retrieves the result
    """

    @dataclass()
    class Element:
        """
        Dataclass for a Monix Element.
        It can be a product or a user
        """
        name: str
        value: int
        isMember: bool

        def __str__(self) -> str:
            return f"• {self.name} (**{self.value}**" + (" coins)" if self.isMember else ")") + "\n"

    disable_warnings(InsecureRequestWarning)
    load_dotenv(".env.dev")
    _JOSIX_LOGIN = getenv("MONIX_LOG", "")
    _JOSIX_PSSWD = getenv("MONIX_PASSWORD", "")
    _LOG_STOCK = getenv("HOME", "") + getenv("LOGS", "") + "stocks.txt"

    def __init__(self, bot: Josix, showHelp: bool):
        super().__init__(showHelp=showHelp)
        self.bot = bot
        self.base_url = "https://monix.clubnix.fr/api"
        self.session = Session()
        self.session.verify = False
        self.generate_token()

    def cog_check(self, ctx: ApplicationContext):
        """
        An automatic check that disable the commands of this extension
        if they are not executed in the server of the Club*Nix
        """
        return ctx.guild.id == 751012516477403176

    def generate_token(self) -> None:
        """
        Method to get the token of the bot and implements it in headers.
        Check if the token is valid with a basic call to the API
        """
        authentication = self.request(
            target="/auth/login",
            method=HTTPMethod.POST,
            json=str({
                "username": Monix._JOSIX_LOGIN,
                "password": Monix._JOSIX_PSSWD
            })
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
            json: str | None = None,
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
        if isinstance(data, dict) and "error" in data:
            raise MonixAPIError(data["error"])

        # Return the data
        return data

    # -----------------------------
    #
    # Bot commands
    #
    # -----------------------------

    @josix_slash(description="Check the current stocks and ping the treasurer if they are low")
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
            # Mention disabled, to enable it uncomment the following lines and add content=text in the ctx.respond
            # roleT = ctx.guild.get_role(1017914272585629788)  # Role of the treasurer
            # text = roleT.mention if roleT else "Role not found"

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
        """
        Compare a value to the top 5 elements

        Parameters
        ----------
        top : list[Element]
            The best elements
        recordVal : int
            The index of the value to compare 

        Returns
        -------
        int
            The index of the element in the top 5. Returns -1 if it does not fit in the top.
        """
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
        return -1

    def compareBottom(self, bottom: list[Element], recordVal: int) -> int:
        """
        Compare a value to the bottom 5 elements

        Parameters
        ----------
        bottom : list[Element]
            The worst elements
        recordVal : int
            The index of the value to comapre

        Returns
        -------
        int
            The index of the element in the bottom 5. Returns -1 if it does not fit in the bottom.
        """
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
        return -1

    @josix_slash(description="Leaderboard of the most and least rich members in Monix")
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
        """
        Get an historic of the transactions made during the last 7 days

        Parameters
        ----------
        isMember : bool
            A boolean to specify if the historic checks the members (or else it's the products) 

        Returns
        -------
        dict[int, Element]
            a dictionary containing all the elements found with their IDs as the key
        """
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
            except KeyError:
                continue

        return elements

    def sortElements(self, elements: list[Element], isMember: bool) -> list[Element]:
        """
        Sort the elements
        This sort is not made to be efficient

        Parameters
        ----------
        elements : list[Element]
            The elements to sort 
        isMember : bool
            Specify if the sort is made on members (or else it's on products)

        Returns
        -------
        list[Element]
            The sorted elements
        """
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

    @josix_slash(description="Ranking of the most consumed products during the last 7 days")
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

    @josix_slash(description="Ranking of the biggest consumers during the last 7 days")
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


def setup(bot: Josix):
    if DISABLE_MONIX:
        return

    bot.add_cog(Monix(bot, True))
