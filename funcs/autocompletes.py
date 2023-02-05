
import discord 
from discord import app_commands
import dynmap.client

async def player_autocomplete(interaction : discord.Interaction, current : str):
    return [
        app_commands.Choice(name=p.name, value=p.name)
        for p in interaction.client.client.get_tracking().players if current.lower() in p.name.lower()
    ][:25]

async def town_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.client.Client = interaction.client.client

    return [
        app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
        for t in client.cached_worlds["RulerEarth"].towns if current.lower().replace("_", " ") in t.name_formatted.lower()
    ][:25]

async def nation_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.client.Client = interaction.client.client

    return [
        app_commands.Choice(name=n.name_formatted, value=n.name_formatted)
        for n in client.cached_worlds["RulerEarth"].nations if current.lower().replace("_", " ") in n.name_formatted.lower()
    ][:25]