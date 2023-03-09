import discord 
from discord.ext import commands

import requests as r
import urllib3

from enum import Enum
from dotenv import load_dotenv
from os import getenv
from urllib3.exceptions import InsecureRequestWarning


urllib3.disable_warnings(InsecureRequestWarning)
load_dotenv()
JOSIX_LOGIN = getenv("monix_log")
JOSIX_PSSWD = getenv("monix_psswd") 

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"

class MonixAPIError(Exception):
    """
    Exception for every Monix API errors
    """


class Monix(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.base_url = "https://monix.clubnix.fr/api"
        self.session = r.Session()
        self.session.verify = False
        
        authentication = self.request(
            target="/auth/login",
            method=HTTPMethod.POST,
            json={
                "username":JOSIX_LOGIN,
                "password":JOSIX_PSSWD
            }
        )

        try:
            self.session.headers = {
                "accept":"application/json",
                "Authorization":f"Bearer {authentication['data']['token']}"
            }
        except KeyError:
            raise MonixAPIError("Error on Josix login")
        print(self.session.headers)


    def request(
        self,
        target: str,
        method: HTTPMethod,
        json: str = None,
        headers: dict = {},
    ) -> dict:
        """
        General-purpose function to create web requests to any API created by Anemys.
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
                headers=headers,
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
            raise MonixAPIError("Access denied (403 Forbidden)")

        # Parse the text into JSON
        try:
            data = data.json()
        except ValueError:
            print(data.text)
            raise MonixAPIError("Unable to parse JSON response")

        # Raise an exception if an error occurred
        if type(data) == dict and "error" in data:
            raise MonixAPIError(data["error"])

        # Return the data
        return data


def setup(bot: commands.Bot):
    bot.add_cog(Monix(bot))