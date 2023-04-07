
import discord 
import datetime

from discord import app_commands
from discord.ext import commands

import dynmap
from dynmap import world as dynmap_w 

from funcs.components import paginator
from funcs import graphs, functions
import setup as s

from matplotlib.pyplot import bar

class Top(commands.Cog):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client

        #super().__init__()

    top = app_commands.Group(name="top", description="List components by ranking")
    top_towns = app_commands.Group(name='towns', parent = top, description='Top towns filter')
    top_nations = app_commands.Group(name='nations', parent = top, description='Top nations filter')
    top_players = app_commands.Group(name='players', parent = top, description='Top players filter')
    top_cultures = app_commands.Group(name="cultures", parent=top, description="Top cultures filter")
    top_religions = app_commands.Group(name="religions", parent=top, description="Top religions filter")

    @top_towns.command(name="activity", description="Towns listed by activity (total time online)")
    async def _towns_activity(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        self.client.world.towns = list(sorted(self.client.world.towns, key=lambda x:x.total_activity, reverse=True))

        description_string = ""
        plottable = {}
        for i, town in enumerate(self.client.world.towns):
            
            plottable[town.name_formatted] = town.total_activity / 60
            description_string += f"{i+1}. {town.name_formatted}: `{functions.generate_time(town.total_activity)}` ({(town.total_activity/self.client.world.total_tracked)*100:,.1f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by online time)", 
            "Town Name", 
            "Minues Online", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(self.client.world.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")
        embed.set_footer(text=f"*Server tracking started {int(self.client.world.total_tracked/3600/24)} days ago.")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @_towns_activity.autocomplete("highlight")
    async def _towns_activity_autocomplete(self, interaction : discord.Interaction, current : str):
        self.client.world.towns = list(sorted(self.client.world.towns, key=lambda x:x.total_activity, reverse=True))

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.world.towns[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_towns.command(name="age", description="Towns listed by age (total age)")
    async def _towns_age(self, interaction : discord.Interaction, reverse : bool = None, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world = self.client.world
        world.towns = list(sorted(world.towns, key=lambda x:x.age, reverse=True if not reverse else False))

        description_string = ""
        plottable = {}
        for i, town in enumerate(world.towns):
            plottable[town.name_formatted] = town.age
            description_string += f"{i+1}. {town.name_formatted}: `{town.age} days` ({town.founded.strftime('%b %d %Y')})\n"

        plottable = dict(graphs.take(35, plottable.items()))
        
        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by age)", 
            "Town Name", 
            "Age (days)", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(world.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @_towns_age.autocomplete("highlight")
    async def _towns_age_highlight(self, interaction : discord.Interaction, current : str):
        world : dynmap_w.World = self.client.world
        world.towns = list(sorted(world.towns, key=lambda x:x.age, reverse=True))

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in world.towns[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_towns.command(name="residents", description="Towns ordered by total residents")
    async def _towns_residents(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.towns = list(sorted(world.towns, key=lambda x:x.total_residents, reverse=True))

        total_residents = world.total_residents

        description_string = ""
        plottable = {}
        for i, town in enumerate(world.towns):
            plottable[town.name_formatted] = town.total_residents
            description_string += f"{i+1}. {town.name_formatted}: `{town.total_residents}` ({(town.total_residents/total_residents)*100:.1f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by total residents)", 
            "Town Name", 
            "Residents", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(world.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    

    @_towns_residents.autocomplete("highlight")
    async def towns_residents_autocomplete(self, interaction : discord.Interaction, current : str):
        world : dynmap_w.World = self.client.world

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.towns, key=lambda x:x.total_residents, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_towns.command(name="area", description="Towns ordered by total area")
    async def _towns_area(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.towns = list(sorted(world.towns, key=lambda x:x.area_km, reverse=True))

        description_string = ""
        plottable = {}
        world_area = world.total_area_km
        for i, town in enumerate(world.towns[1:]):
            town_area = town.area_km
            plottable[town.name_formatted] = (town_area*(1000^2))/256
            description_string += f"{i+1}. {town.name_formatted}: `{(town_area*(1000^2))/256:,.0f} plots` ({town_area:,.2f}km²) ({(town_area/world_area)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by total claimed area)", 
            "Town Name", 
            "Claimed Area (plots)", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(world.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    

    @_towns_area.autocomplete("highlight")
    async def towns_area_autocomplete(self, interaction : discord.Interaction, current : str):
        world : dynmap_w.World = self.client.world

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.towns, key=lambda x:x.total_residents, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    

    @top_nations.command(name="residents", description="Nations ordered by total residents")
    async def _nations_residents(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.nations = list(sorted(world.nations, key=lambda x:x.total_residents, reverse=True))

        description_string = ""
        plottable = {}
        for i, nation in enumerate(world.nations):
            plottable[nation.name_formatted] = nation.total_residents
            description_string += f"{i+1}. {nation.name_formatted}: `{nation.total_residents}` ({(nation.total_residents/world.total_residents)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top nations (by total residents)", 
            "Nation Name", 
            "Residents", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="nations_graph.png")
    
        embed = discord.Embed(title=f"Nations ({len(world.nations)})", color=s.embed)
        embed.set_image(url="attachment://nations_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @top_towns.command(name="balance", description="Towns ordered by bank balance")
    async def _towns_balance(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.towns = list(sorted(world.towns, key=lambda x:x.bank, reverse=True))

        total_balance = world.total_town_bank

        description_string = ""
        plottable = {}
        for i, town in enumerate(world.towns):
            plottable[town.name_formatted] = town.bank
            description_string += f"{i+1}. {town.name_formatted}: `${town.bank:,.2f}` ({(town.bank/total_balance)*100:.1f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top towns (by bank balance)", 
            "Town Name", 
            "Bank Balance", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="towns_graph.png")
    
        embed = discord.Embed(title=f"Towns ({len(world.towns)})", color=s.embed)
        embed.set_image(url="attachment://towns_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    

    @_towns_residents.autocomplete("highlight")
    async def towns_balance(self, interaction : discord.Interaction, current : str):
        world : dynmap_w.World = self.client.world

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.towns, key=lambda x:x.bank, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    

    @_nations_residents.autocomplete("highlight")
    async def nations_residents_autocomplete_nation(self, interaction : discord.Interaction, current : str):
        world = self.client.world

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.nations, key=lambda x:x.total_residents, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_players.command(name="activity", description="All players who have joined the server while tracking")
    async def _players_activity(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        await interaction.response.defer()

        self.client.world.players = list(sorted(self.client.world.players, key = lambda x: x.total_online, reverse=True))

        description_string = ""
        for i, player in enumerate(self.client.world.players):
            bold = ""
            if player.last_online + datetime.timedelta(seconds=s.REFRESH_INTERVAL+10) >= datetime.datetime.now():
                bold = "**"

            percent = (player.total_online / self.client.world.total_tracked) * 100
            description_string += f"{i+1}. {bold}{discord.utils.escape_markdown(player.name)}{bold}: `{functions.generate_time(player.total_online)}` <t:{round(player.last_online.timestamp())}:R> ({percent:,.1f}%)\n"

        plottable = {}
        for player in self.client.world.players:
            plottable[player.name] = player.total_online / 60
        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top players (by time in world)", 
            "Player", 
            "Minutes on earth", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="players_graph.png")
    
        embed = discord.Embed(title=f"Players ({len(self.client.world.players)})", color=s.embed)
        embed.set_image(url="attachment://players_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @_players_activity.autocomplete("highlight")
    async def _top_players_highlight(self, interaction : discord.Interaction, current : str):
        self.client.world.players = list(sorted(self.client.world.players, key = lambda x: x.total_online, reverse=True))

        return [
            app_commands.Choice(name=t.name, value=t.name)
            for t in self.client.world.players[:25] if current.lower() in t.name.lower()
        ][:25]
    
    @top_nations.command(name="area", description="Nations ordered by total claimed area")
    async def _nations_area(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.nations = list(sorted(world.nations, key=lambda x:x.area_km, reverse=True))

        description_string = ""
        plottable = {}
        world_area = world.total_area_km
        for i, nation in enumerate(world.nations):
            nation_area = nation.area_km
            plottable[nation.name_formatted] = (nation_area*(1000^2))/256
            description_string += f"{i+1}. {nation.name_formatted}: `{(nation_area*(1000^2))/256:,.0f} plots` ({nation_area:,.2f}km²) ({(nation_area/world_area)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top nations (by claimed area)", 
            "Nation Name", 
            "Claimed Area (plots)", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="nations_graph.png")
    
        embed = discord.Embed(title=f"Nations ({len(world.nations)})", color=s.embed)
        embed.set_image(url="attachment://nations_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    

    @_nations_area.autocomplete("highlight")
    async def nations_area_autocomplete_nation(self, interaction : discord.Interaction, current : str):
        world = self.client.world

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.nations, key=lambda x:x.area_km, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_nations.command(name="towns", description="Nations ordered by total town count")
    async def _nations_towns(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.nations = list(sorted(world.nations, key=lambda x:len(x.towns), reverse=True))

        description_string = ""
        plottable = {}
        for i, nation in enumerate(world.nations):
            plottable[nation.name_formatted] = len(nation.towns)
            description_string += f"{i+1}. {nation.name_formatted}: `{len(nation.towns)} towns` ({(len(nation.towns)/len(world.towns))*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top nations (by total towns)", 
            "Nation Name", 
            "Town Total", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="nations_graph.png")
    
        embed = discord.Embed(title=f"Nations ({len(world.nations)})", color=s.embed)
        embed.set_image(url="attachment://nations_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    

    @_nations_towns.autocomplete("highlight")
    async def nations_towns_highlight_nation(self, interaction : discord.Interaction, current : str):
        world = self.client.world

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in list(sorted(world.nations, key=lambda x:x.area_km, reverse=True))[:25] if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @top_players.command(name="visited_towns", description="Rank players by number of visited towns")
    async def _players_visited_towns(self, interaction : discord.Interaction, highlight : str = None):

        #print_here

        await interaction.response.defer()

        self.client.world.players = list(sorted(self.client.world.players, key = lambda x: len(x.visited), reverse=True))

        description_string = ""
        for i, player in enumerate(self.client.world.players):

            percent = (len(player.visited) / len(self.client.world.towns)) * 100
            description_string += f"{i+1}. {discord.utils.escape_markdown(player.name)}: `{len(player.visited)}` ({percent:,.1f}%)\n"

        plottable = {}
        for player in self.client.world.players:
            plottable[player.name] = len(player.visited)
        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top players (by visited town count)", 
            "Player", 
            "Town count", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="players_graph.png")
    
        embed = discord.Embed(title=f"Players ({len(self.client.world.players)})", color=s.embed)
        embed.set_image(url="attachment://players_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @_players_activity.autocomplete("highlight")
    async def _top_players_highlight(self, interaction : discord.Interaction, current : str):
        self.client.world.players = list(sorted(self.client.world.players, key = lambda x: x.total_online, reverse=True))

        return [
            app_commands.Choice(name=t.name, value=t.name)
            for t in self.client.world.players[:25] if current.lower() in t.name.lower()
        ][:25]
    
    # Cultures

    @top_cultures.command(name="residents", description="Cultures ordered by total residents of towns ")
    async def _cultures_residents(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.cultures = list(sorted(world.cultures, key=lambda x:x.total_residents, reverse=True))

        description_string = ""
        plottable = {}
        for i, culture in enumerate(world.cultures):
            plottable[culture.name] = culture.total_residents
            description_string += f"{i+1}. {culture.name}: `{culture.total_residents}` ({(culture.total_residents/world.total_residents)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top cultures (by total residents)", 
            "Culture Name", 
            "Residents", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="cultures_graph.png")
    
        embed = discord.Embed(title=f"Cultures ({len(world.cultures)})", color=s.embed)
        embed.set_image(url="attachment://cultures_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)

    @_cultures_residents.autocomplete("highlight")
    async def cultures_residents_autocomplete_culture(self, interaction : discord.Interaction, current : str):
        world = self.client.world

        return [
            app_commands.Choice(name=c.name, value=c.name)
            for c in list(sorted(world.cultures, key=lambda x: x.total_residents, reverse=True))[:25] if current.lower() in c.name.lower()
        ][:25]
    
    @top_cultures.command(name="towns", description="Cultures ordered by total town count ")
    async def _cultures_towns(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.cultures = list(sorted(world.cultures, key=lambda x:len(x.towns), reverse=True))

        description_string = ""
        plottable = {}
        for i, culture in enumerate(world.cultures):
            plottable[culture.name] = len(culture.towns)
            description_string += f"{i+1}. {culture.name}: `{len(culture.towns)}` ({(len(culture.towns)/len(world.towns))*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top cultures (by town count)", 
            "Culture Name", 
            "Towns", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="cultures_graph.png")
    
        embed = discord.Embed(title=f"Cultures ({len(world.cultures)})", color=s.embed)
        embed.set_image(url="attachment://cultures_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)

    @_cultures_towns.autocomplete("highlight")
    async def cultures_towns_autocomplete_culture(self, interaction : discord.Interaction, current : str):
        world = self.client.world

        return [
            app_commands.Choice(name=c.name, value=c.name)
            for c in list(sorted(world.cultures, key=lambda x: len(x.towns), reverse=True))[:25] if current.lower() in c.name.lower()
        ][:25]
    
    # Religions

    @top_religions.command(name="followers", description="Religions ordered by total follower count ")
    async def _religions_residents(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.religions = list(sorted(world.religions, key=lambda x:x.total_followers, reverse=True))

        description_string = ""
        plottable = {}
        for i, religion in enumerate(world.religions):
            plottable[religion.name] = religion.total_followers
            description_string += f"{i+1}. {religion.name}: `{religion.total_followers}` ({(religion.total_followers/world.total_residents)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top religions (by total followers)", 
            "Religion Name", 
            "Followers", 
            bar,
            highlight=highlight
        )
        
        graph = discord.File(file_name, filename="religions_graph.png")
    
        embed = discord.Embed(title=f"Religions ({len(world.religions)})", color=s.embed)
        embed.set_image(url="attachment://religions_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)

    @_religions_residents.autocomplete("highlight")
    async def religions_residents_autocomplete_religion(self, interaction : discord.Interaction, current : str):
        world = self.client.world

        return [
            app_commands.Choice(name=r.name, value=r.name)
            for r in list(sorted(world.religions, key=lambda x: x.total_followers, reverse=True))[:25] if current.lower() in r.name.lower()
        ][:25]
    
    @top_religions.command(name="towns", description="Religions ordered by total town count ")
    async def _religions_towns(self, interaction : discord.Interaction, highlight : str = None):

        #print_here
        await interaction.response.defer()
        world : dynmap_w.World = self.client.world
        world.religions = list(sorted(world.religions, key=lambda x:len(x.towns), reverse=True))

        description_string = ""
        plottable = {}
        for i, religion in enumerate(world.religions):
            plottable[religion.name] = len(religion.towns)
            description_string += f"{i+1}. {religion.name}: `{len(religion.towns)}` ({(len(religion.towns)/len(world.towns))*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        if highlight and highlight in list(plottable.keys()):
            highlight = list(plottable.keys()).index(highlight)
        else:
            highlight = None

        file_name = graphs.save_graph(
            plottable, 
            "Top religions (by town count)", 
            "Religion Name", 
            "Towns", 
            bar,
            highlight=highlight
        )
        graph = discord.File(file_name, filename="religions_graph.png")
    
        embed = discord.Embed(title=f"Religions ({len(world.religions)})", color=s.embed)
        embed.set_image(url="attachment://religions_graph.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)

    @_religions_towns.autocomplete("highlight")
    async def religions_towns_highlight(self, interaction : discord.Interaction, current : str):
        world = self.client.world

        return [
            app_commands.Choice(name=r.name, value=r.name)
            for r in list(sorted(world.religions, key=lambda x: len(x.towns), reverse=True))[:25] if current.lower() in r.name.lower()
        ][:25]


    
async def setup(bot : commands.Bot):
    await bot.add_cog(Top(bot, bot.client))





