
import discord 
import datetime

from discord import app_commands
from discord.ext import commands

from matplotlib.pyplot import bar, plot

import dynmap
from dynmap import world as w
from dynmap import errors as e

from funcs.components import paginator
from funcs import graphs, functions, autocompletes
import setup as s

class History(commands.Cog):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client
    
    history = app_commands.Group(name="history", description="Get historic statistics for towns and players")
    history_town = app_commands.Group(name='town', parent = history, description='History for town stats')
    history_player = app_commands.Group(name="player", parent=history, description="History for players")

    @history_town.command(name="bank", description="Bank history over time")
    async def _bank_history(self, interaction : discord.Interaction, town : str):

        #print_here
        await interaction.response.defer()
        town : w.Town = self.client.world.get_town(town.replace(" ", "_"), case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")

        description_string = ""
        for day, balance in reversed(town.bank_history.items()):
            description_string += f"**{day}**: ${balance:,.2f}\n"

        file_name = graphs.save_graph(town.bank_history, f"{town.name_formatted} bank history", "Date", "Balance ($)", plot)
        graph = discord.File(file_name, filename="town_bank_graph.png")

        embed = discord.Embed(title="Town Bank History", color=s.embed)
        embed.set_image(url="attachment://town_bank_graph.png")
        embed.set_footer(text=f"*Server tracking started {int(self.client.world.total_tracked/3600/24)} days ago.")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)

    @_bank_history.autocomplete("town")
    async def _town_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.world.towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @history_town.command(name="visitors", description="All players who visited the town")
    async def _visitors(self, interaction : discord.Interaction, town : str):

        #print_here

        await interaction.response.defer()

        town : w.Town = self.client.world.get_town(town.replace(" ", "_"), case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")

        town.visited = dict(sorted(town.visited.items(), key=lambda x: x[1]["total"], reverse=True))

        description_string = ""
        for i, (name, data) in enumerate(town.visited.items()):
            
            bold = ""
            if data['last'] + datetime.timedelta(seconds=s.REFRESH_INTERVAL + 10) >= datetime.datetime.now():
                bold = "**"
            r = self.client.world.get_player(name)
            likely_residency = r.likely_residency if r else None
            rsTag = ""
            if likely_residency and likely_residency == town:
                rsTag = "`[R]` "

            description_string += f"{i+1}. {rsTag}{bold}{discord.utils.escape_markdown(name)}{bold}: `{functions.generate_time(data['total'])}` <t:{round(data['last'].timestamp())}:R>\n"

        plottable = {}
        for name, activity in town.visited.items():
            plottable[name] = activity["total"] / 60

        plottable = dict(graphs.take(25, plottable.items()))

        file_name = graphs.save_graph(
            plottable, 
            f"{town.name_formatted} top visitors (by time)", 
            "Player", 
            "Minutes visiting", 
            bar
        )
        graph = discord.File(file_name, filename="town_visitors_graph.png")
    
        embed = discord.Embed(title=f"Town historic visitors ({len(town.visited)})", color=s.embed)
        embed.set_image(url="attachment://town_visitors_graph.png")
        embed.set_footer(text=f"*Server tracking started {int(self.client.world.total_tracked/3600/24)} days ago.")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @_visitors.autocomplete("town")
    async def _visitors_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.world.towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @history_town.command(name="residents", description="A total of residents for a town over time")
    async def _residents(self, interaction : discord.Interaction, town : str):

        #print_here
        await interaction.response.defer()
        town : w.Town = self.client.world.get_town(town.replace(" ", "_"), case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")

        description_string = ""
        for date, data in reversed(town.total_residents_history.items()):
            description_string += f"**{date}**: {data} residents\n"

        file_name = graphs.save_graph(town.total_residents_history, f"{town.name_formatted} total resident history", "Date", "Total residents", plot)
        graph = discord.File(file_name, filename="town_resident_history.png")

        embed = discord.Embed(title="Town resident count", color=s.embed)
        embed.set_image(url="attachment://town_resident_history.png")
        embed.set_footer(text=f"*Server tracking started {int(self.client.world.total_tracked/3600/24)} days ago.")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @_residents.autocomplete("town")
    async def _residents_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.world.towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @history_player.command(name="visited_towns", description="History for towns this player has visited")
    @app_commands.autocomplete(player=autocompletes.player_autocomplete)
    async def _visited_towns(self, interaction : discord.Interaction, player : str):

        #print_here

        await interaction.response.defer()

        player : w.Player = self.client.world.get_player(player, case_sensitive=False)

        if not player:
            raise e.MildError("Player not found")

        visited = dict(sorted(player.visited.items(), key=lambda x: x[1]["total"], reverse=True))

        description_string = ""
        for i, (town_name, data) in enumerate(visited.items()):
            bold = ""
            if data['last'] + datetime.timedelta(seconds=s.REFRESH_INTERVAL + 10) >= datetime.datetime.now():
                bold = "**"

            description_string += f"{i+1}. {bold}{town_name}{bold}: `{functions.generate_time(data['total'])}` <t:{round(data['last'].timestamp())}:R>\n"

        plottable = {}
        for town_name, activity in visited.items():
            plottable[town_name] = activity["total"] / 60

        plottable = dict(graphs.take(25, plottable.items()))

        file_name = graphs.save_graph(
            plottable, 
            f"{player.name} visited towns (by time)", 
            "Town", 
            "Minutes visiting", 
            bar
        )
        graph = discord.File(file_name, filename="player_visited_graph.png")
    
        embed = discord.Embed(title=f"Player visited towns ({len(visited)})", color=s.embed)
        embed.set_image(url="attachment://player_visited_graph.png")
        embed.set_footer(text=f"*Server tracking started {int(self.client.world.total_tracked/3600/24)} days ago.")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)

    
async def setup(bot : commands.Bot):
    await bot.add_cog(History(bot, bot.client))





