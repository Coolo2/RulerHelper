
import discord 
import datetime

from discord import app_commands
from discord.ext import commands

import dynmap
from dynmap import world as dynmap_w 

from funcs.components import paginator
from funcs import graphs, functions
import setup as s

import matplotlib.pyplot as plt

class Top(commands.Cog):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client

        #super().__init__()

    top = app_commands.Group(name="top", description="List components by ranking")
    top_towns = app_commands.Group(name='towns', parent = top, description='Top towns filter')
    top_nations = app_commands.Group(name='nations', parent = top, description='Top nations filter')
    top_players = app_commands.Group(name='players', parent = top, description='Top players filter')

    @top_towns.command(name="activity", description="Towns listed by activity (total time online)")
    async def _towns_activity(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        tracking = self.client.get_tracking()

        tracking.towns = list(sorted(tracking.towns, key=lambda x:x.get_total_activity(), reverse=True))

        description_string = ""
        plottable = {}
        for i, town in enumerate(tracking.towns):
            if not town.town:
                continue
            
            plottable[town.town.name_formatted] = town.get_total_activity() / 60
            description_string += f"{i+1}. {town.town.name_formatted}: `{functions.generate_time(town.get_total_activity())}` ({(town.get_total_activity()/tracking.total_tracked_seconds)*100:,.1f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight:
            highlight = list(plottable.keys()).index(highlight)

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by online time)", 
            "Town Name", 
            "Minues Online", 
            plt.bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(tracking.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")
        embed.set_footer(text=f"*Server tracking started {int(tracking.total_tracked_seconds/3600/24)} days ago.")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.response.send_message(embed=view.embed, view=view, file=graph)
    
    @_towns_activity.autocomplete("highlight")
    async def _towns_activity_autocomplete(self, interaction : discord.Interaction, current : str):
        tracking = self.client.get_tracking()
        tracking.towns = list(sorted(tracking.towns, key=lambda x:x.get_total_activity(), reverse=True))

        return [
            app_commands.Choice(name=t.town.name_formatted, value=t.town.name_formatted)
            for t in tracking.towns[:25] if current.lower().replace("_", " ") in t.town.name_formatted.lower()
        ][:25]
    
    @top_towns.command(name="residents", description="Towns ordered by total residents")
    async def _towns_residents(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        world.towns = list(sorted(world.towns, key=lambda x:x.total_residents, reverse=True))

        total_residents = world.total_residents

        description_string = ""
        plottable = {}
        for i, town in enumerate(world.towns):
            plottable[town.name_formatted] = town.total_residents
            description_string += f"{i+1}. {town.name_formatted}: `{town.total_residents}` ({(town.total_residents/total_residents)*100:.1f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight:
            highlight = list(plottable.keys()).index(highlight)

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by total residents)", 
            "Town Name", 
            "Residents", 
            plt.bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(world.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.response.send_message(embed=view.embed, view=view, file=graph)
    

    @_towns_residents.autocomplete("highlight")
    async def towns_residents_autocomplete(self, interaction : discord.Interaction, current : str):
        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.towns, key=lambda x:x.total_residents, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_towns.command(name="area", description="Towns ordered by total area")
    async def _towns_area(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        world.towns = list(sorted(world.towns, key=lambda x:x.area_km, reverse=True))

        description_string = ""
        plottable = {}
        world_area = world.total_area_km
        for i, town in enumerate(world.towns[1:]):
            town_area = town.area_km
            plottable[town.name_formatted] = (town_area*(1000^2))/256
            description_string += f"{i+1}. {town.name_formatted}: `{(town_area*(1000^2))/256:,.0f} plots` ({town_area:,.2f}km²) ({(town_area/world_area)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight:
            highlight = list(plottable.keys()).index(highlight)

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by total claimed area)", 
            "Town Name", 
            "Claimed Area (plots)", 
            plt.bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(world.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.response.send_message(embed=view.embed, view=view, file=graph)
    

    @_towns_area.autocomplete("highlight")
    async def towns_area_autocomplete(self, interaction : discord.Interaction, current : str):
        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.towns, key=lambda x:x.total_residents, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    

    @top_nations.command(name="residents", description="Nations ordered by total residents")
    async def _nations_residents(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        world.nations = list(sorted(world.nations, key=lambda x:x.total_residents, reverse=True))

        description_string = ""
        plottable = {}
        for i, nation in enumerate(world.nations):
            plottable[nation.name_formatted] = nation.total_residents
            description_string += f"{i+1}. {nation.name_formatted}: `{nation.total_residents}` ({(nation.total_residents/world.total_residents)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight:
            highlight = list(plottable.keys()).index(highlight)

        file_name = graphs.save_graph(
            plottable, 
            "Top nations (by total residents)", 
            "Nation Name", 
            "Residents", 
            plt.bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="nations_graph.png")
    
        embed = discord.Embed(title=f"Nations ({len(world.nations)})", color=s.embed)
        embed.set_image(url="attachment://nations_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.response.send_message(embed=view.embed, view=view, file=graph)
    

    @_nations_residents.autocomplete("highlight")
    async def nations_residents_autocomplete_nation(self, interaction : discord.Interaction, current : str):
        world = self.client.cached_worlds["RulerEarth"]

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.nations, key=lambda x:x.total_residents, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_players.command(name="activity", description="All players who have joined the server while tracking")
    async def _players_activity(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        await interaction.response.defer()

        tracking = self.client.get_tracking()

        tracking.players = list(sorted(tracking.players, key = lambda x: x.total_online_seconds, reverse=True))

        description_string = ""
        for i, player in enumerate(tracking.players):
            bold = ""
            if player.last_seen_timestamp + 30 >= datetime.datetime.now().timestamp():
                bold = "**"

            percent = (player.total_online_seconds / player.tracking.total_tracked_seconds) * 100
            description_string += f"{i+1}. {bold}{player.name}{bold}: `{functions.generate_time(player.total_online_seconds)}` <t:{round(player.last_seen_timestamp)}:R> ({percent:,.1f}%)\n"

        plottable = {}
        for player in tracking.players:
            plottable[player.name] = player.total_online_seconds / 60
        plottable = dict(graphs.take(25, plottable.items()))

        if highlight:
            highlight = list(plottable.keys()).index(highlight)

        file_name = graphs.save_graph(
            plottable, 
            "Top players (by time in world)", 
            "Player", 
            "Minutes on earth", 
            plt.bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="players_graph.png")
    
        embed = discord.Embed(title=f"Players ({len(tracking.players)})", color=s.embed)
        embed.set_image(url="attachment://players_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @_players_activity.autocomplete("highlight")
    async def _top_players_highlight(self, interaction : discord.Interaction, current : str):
        tracking = self.client.get_tracking()
        tracking.players = list(sorted(tracking.players, key = lambda x: x.total_online_seconds, reverse=True))

        return [
            app_commands.Choice(name=t.name, value=t.name)
            for t in tracking.players[:25] if current.lower() in t.name.lower()
        ][:25]
    
    @top_nations.command(name="area", description="Nations ordered by total claimed area")
    async def _nations_area(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        world.nations = list(sorted(world.nations, key=lambda x:x.area_km, reverse=True))

        description_string = ""
        plottable = {}
        world_area = world.total_area_km
        for i, nation in enumerate(world.nations):
            nation_area = nation.area_km
            plottable[nation.name_formatted] = (nation_area*(1000^2))/256
            description_string += f"{i+1}. {nation.name_formatted}: `{(nation_area*(1000^2))/256:,.0f} plots` ({nation_area:,.2f}km²) ({(nation_area/world_area)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight:
            highlight = list(plottable.keys()).index(highlight)

        file_name = graphs.save_graph(
            plottable, 
            "Top nations (by claimed area)", 
            "Nation Name", 
            "Claimed Area (plots)", 
            plt.bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="nations_graph.png")
    
        embed = discord.Embed(title=f"Nations ({len(world.nations)})", color=s.embed)
        embed.set_image(url="attachment://nations_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.response.send_message(embed=view.embed, view=view, file=graph)
    

    @_nations_area.autocomplete("highlight")
    async def nations_area_autocomplete_nation(self, interaction : discord.Interaction, current : str):
        world = self.client.cached_worlds["RulerEarth"]

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.nations, key=lambda x:x.area_km, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]


    
async def setup(bot : commands.Bot):
    await bot.add_cog(Top(bot, bot.client))





