
import discord 
from discord import app_commands
import dynmap

async def player_autocomplete(interaction : discord.Interaction, current : str):

    return [
        app_commands.Choice(name=p.name, value=p.name)
        for p in interaction.client.client.world.players if current.lower() in p.name.lower()
    ][:25]

async def town_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.Client = interaction.client.client

    return [
        app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
        for t in client.world.towns if current.lower().replace("_", " ") in t.name_formatted.lower()
    ][:25]

async def nation_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.Client = interaction.client.client

    return [
        app_commands.Choice(name=n.name_formatted, value=n.name_formatted)
        for n in client.world.nations if current.lower().replace("_", " ") in n.name_formatted.lower()
    ][:25]

async def culture_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.Client = interaction.client.client

    return [
        app_commands.Choice(name=c.name[:50], value=c.name[:50])
        for c in client.world.cultures if current.lower() in c.name.lower()
    ][:25]

async def religion_autocomplete(interaction : discord.Interaction, current : str):
    client : dynmap.Client = interaction.client.client

    return [
        app_commands.Choice(name=r.name[:50], value=r.name[:50])
        for r in client.world.religions if current.lower() in r.name.lower()
    ][:25]