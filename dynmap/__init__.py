

import discord
from discord.ext import commands

from dynmap import http
from dynmap import world

import typing

class Client():
    def __init__(self, bot : typing.Union[discord.Client, commands.Bot], url : str):
        self.url = url

        self.bot = bot

        self.http : http.HTTP = http.HTTP(self)

        self.world : world.World = None
