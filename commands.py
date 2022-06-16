
import dynmap

# '2.0.0a'
import discord 

from discord.ext import commands
from discord import app_commands
import setup as s 
import os

import cogs.tasks

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(s.default_prefix, intents=intents)
client = dynmap.Client(bot, "https://map.rulercraft.com")

tree : app_commands.CommandTree = bot.tree
bot.client = client 

@bot.event 
async def on_ready():

    if s.refresh_commands:
        await tree.sync()

        for guild in s.slash_guilds:
            await tree.sync(guild=guild)
    
    cogs.tasks.get_world_task(bot, client).start()

extensions = [file.replace(".py", "") for file in os.listdir('./cmds') if file.endswith(".py")]

async def setup_hook():
    for extension in extensions:
        await bot.load_extension(f"cmds.{extension}")

    await bot.load_extension("cogs.events")

bot.setup_hook = setup_hook

bot.run(os.getenv("token"))