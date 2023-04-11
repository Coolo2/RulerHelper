
import dynmap

# '2.0.0a'
import discord 

from discord.ext import commands
from discord import app_commands
import setup as s 
import os

import asyncio
import cogs.tasks
import aiofiles

import dotenv 
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot("", intents=intents)
client = dynmap.Client(bot, "https://map.rulercraft.com")

tree : app_commands.CommandTree = bot.tree
bot.client = client 

@bot.event 
async def on_ready():
    print(f"Bot ({bot.user}) Online!")
    
extensions = [file.replace(".py", "") for file in os.listdir('./cmds') if file.endswith(".py")]

async def setup_hook():

    if not os.path.exists("rulercraft/config.json"):
        async with aiofiles.open("rulercraft/config.json", "w") as f:
            await f.write("{}")
    
    for extension in extensions:
        await bot.load_extension(f"cmds.{extension}")

    if s.PRODUCTION_MODE:
        await bot.load_extension("cogs.errors")
    await bot.load_extension("cogs.events")

    if s.refresh_commands:
        await tree.sync()

        for guild in s.slash_guilds:
            try:
                await tree.sync(guild=guild)
            except:
                print(f"Couldn't sync commands to {guild.id}")

    # Run the refresher
    if s.MULTI_THREAD_MODE:
        import task
        import threading 

        t = threading.Thread(target=task.periodic, args=(client,))
        t.start()
        await asyncio.sleep(10)
        cogs.tasks.notifications_task(bot, client).start()
    else:
        cogs.tasks.load_and_update_file_task(bot, client).start()

bot.setup_hook = setup_hook

bot.run(os.getenv("token"))