
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

async def culture_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.client.Client = interaction.client.client

    return [
        app_commands.Choice(name=c.name[:50], value=c.name[:50])
        for c in client.cached_worlds["RulerEarth"].cultures if current.lower() in c.name.lower()
    ][:25]

async def religion_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.client.Client = interaction.client.client

    return [
        app_commands.Choice(name=r.name[:50], value=r.name[:50])
        for r in client.cached_worlds["RulerEarth"].religions if current.lower() in r.name.lower()
    ][:25]