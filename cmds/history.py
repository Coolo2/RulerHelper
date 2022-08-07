
import discord 
import datetime

from discord import app_commands
from discord.ext import commands

import matplotlib.pyplot as plt

import dynmap
from dynmap import tracking as dynmap_t
from dynmap import errors as e

from funcs.components import paginator
from funcs import graphs
from funcs import functions
import setup as s

class History(commands.Cog):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client
    
    history = app_commands.Group(name="history", description="Get historic statistics for towns and players")
    history_town = app_commands.Group(name='town', parent = history, description='History for town stats')

    @history_town.command(name="bank", description="Bank history over time")
    async def _bank_history(self, interaction : discord.Interaction, town : str):

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")

        tracking = self.client.get_tracking()
        town : dynmap_t.TrackTown = tracking.get_town(town.replace(" ", "_"), case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")

        description_string = ""
        for day, balance in reversed(town.bank_history.items()):
            description_string += f"**{day}**: ${balance:,.2f}\n"

        file_name = graphs.save_graph(town.bank_history, f"{town.town.name_formatted} bank history", "Date", "Balance ($)", plt.plot)
        graph = discord.File(file_name, filename="town_bank_graph.png")

        embed = discord.Embed(title="Town Bank History", color=s.embed)
        embed.set_image(url="attachment://town_bank_graph.png")

        per_page = 10

        pages = description_string.split("\n")
        pages = ["\n".join(pages[i:i+per_page]) for i in range(0, len(pages), per_page)]

        embed.description = pages[0]
        embed.set_footer(text=f"*Server tracking started {round(tracking.total_tracked_seconds/3600/24)} days ago.")

        view = paginator.PaginatorView(pages, embed)

        await interaction.response.send_message(embed=embed, view=view, file=graph)

        msg = await interaction.original_message()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.url, label="Copy/Zoom Image", url=msg.embeds[0].image.url, row=2))
        await msg.edit(
            view=view
        )

    @_bank_history.autocomplete("town")
    async def _town_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.cached_worlds["RulerEarth"].towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @history_town.command(name="visitors", description="All players who visited the town")
    async def _visitors(self, interaction : discord.Interaction, town : str):

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")

        await interaction.response.defer()

        tracking = self.client.get_tracking()
        town : dynmap_t.TrackTown = tracking.get_town(town.replace(" ", "_"), case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")

        town.visited = dict(sorted(town.visited.items(), key=lambda x: x[1]["total"], reverse=True))

        description_string = ""
        for i, (name, data) in enumerate(town.visited.items()):
            bold = ""
            if data['last'] + 30 >= datetime.datetime.now().timestamp():
                bold = "**"
            likely_residency = self.client.get_tracking().get_player(name).get_likely_residency()
            rsTag = ""
            if likely_residency and likely_residency.town and likely_residency.town.name == town.town.name:
                rsTag = "`[R]` "

            description_string += f"{i+1}. {rsTag}{bold}{name}{bold}: `{functions.generate_time(data['total'])}` <t:{round(data['last'])}:R>\n"

        plottable = {}
        for name, activity in town.visited.items():
            plottable[name] = activity["total"] / 60

        plottable = dict(graphs.take(25, plottable.items()))

        file_name = graphs.save_graph(
            plottable, 
            f"{town.town.name_formatted} top visitors (by time)", 
            "Player", 
            "Minutes visiting", 
            plt.bar
        )
        graph = discord.File(file_name, filename="town_visitors_graph.png")
    
        embed = discord.Embed(title=f"Town historic visitors ({len(town.visited)})", color=s.embed)
        embed.set_image(url="attachment://town_visitors_graph.png")

        per_page = 10

        pages = description_string.split("\n")
        pages = ["\n".join(pages[i:i+per_page]) for i in range(0, len(pages), per_page)]

        embed.description = pages[0]
        embed.set_footer(text=f"*Server tracking started {round(tracking.total_tracked_seconds/3600/24)} days ago.")

        view = paginator.PaginatorView(pages, embed)

        await interaction.followup.send(embed=embed, view=view, file=graph)

        msg = await interaction.original_message()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.url, label="Copy/Zoom Image", url=msg.embeds[0].image.url, row=2))
        await msg.edit(
            view=view
        )
    
    @_visitors.autocomplete("town")
    async def _visitors_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.cached_worlds["RulerEarth"].towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @history_town.command(name="total_residents", description="A total of residents for a town over time")
    async def _residents(self, interaction : discord.Interaction, town : str):

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")

        tracking = self.client.get_tracking()
        town : dynmap_t.TrackTown = tracking.get_town(town.replace(" ", "_"), case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")

        description_string = ""
        for date, data in reversed(town.total_residents_history.items()):
            description_string += f"**{date}**: {data} residents\n"

        file_name = graphs.save_graph(town.total_residents_history, f"{town.town.name_formatted} total resident history", "Date", "Total residents", plt.plot)
        graph = discord.File(file_name, filename="town_resident_history.png")

        embed = discord.Embed(title="Town resident count", color=s.embed)
        embed.set_image(url="attachment://town_resident_history.png")

        per_page = 10

        pages = description_string.split("\n")
        pages = ["\n".join(pages[i:i+per_page]) for i in range(0, len(pages), per_page)]

        embed.description = pages[0]
        embed.set_footer(text=f"*Server tracking started {round(tracking.total_tracked_seconds/3600/24)} days ago.")

        view = paginator.PaginatorView(pages, embed)

        await interaction.response.send_message(embed=embed, view=view, file=graph)

        msg = await interaction.original_message()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.url, label="Copy/Zoom Image", url=msg.embeds[0].image.url, row=2))
        await msg.edit(
            view=view
        )
    
    @_residents.autocomplete("town")
    async def _residents_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.cached_worlds["RulerEarth"].towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]

    
async def setup(bot : commands.Bot):
    await bot.add_cog(History(bot, bot.client))





