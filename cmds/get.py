
import discord 
import json
import io

from discord import app_commands
from discord.ext import commands

import dynmap
from dynmap import world as dynmap_w 

from funcs.components import paginator, commands_view, towns_view
import setup as s

from dynmap import errors as e

from funcs import functions, graphs, autocompletes

from matplotlib.pyplot import pie

class Get(commands.GroupCog, name="get", description="All get commands"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client

        super().__init__()

    
    @app_commands.command(name="online", description="Get online members and their positions")
    async def _online(self, interaction : discord.Interaction):

        #print_here

        await interaction.response.defer()

        world : dynmap_w.World = self.client.world
        embed = discord.Embed(title=f"Online players ({len(world.online_players)})",
            color=s.embed)
        
        file_name = graphs.plot_world(world, True)
        graph = discord.File(file_name, filename="world_map.png")

        description_string = ""
        for player in world.online_players:
            description_string += f"**{discord.utils.escape_markdown(player.name)}**:    [{player.x:,d}, {player.y:,d}, {player.z:,d}]({self.client.url}?x={player.x}&z={player.z}&zoom=8) (`{round((player.total_online / world.total_tracked) * 100)}%`)\n"
        
        embed.set_image(url="attachment://world_map.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @app_commands.command(name="player", description="Get info for a specific player")
    @app_commands.autocomplete(player=autocompletes.player_autocomplete)
    async def _player(self, interaction : discord.Interaction, player : str):

        #print_here

        world : dynmap_w.World = self.client.world
        player : dynmap_w.Player = world.get_player(player, case_sensitive=False)

        if not player:
            raise e.MildError("Player not found")

        embed = discord.Embed(title=f"Player: {player.name}",
                color=s.embed)

        likely_residency = player.likely_residency
        notable_statistics = player.get_notable_statistics()

        if not player.online:
            embed.description = "*Player is offline, using last seen data.*"

        embed.add_field(name="Health", value=player.health)
        embed.add_field(name="Armour", value=player.armor)
        embed.add_field(name="Coordinates", value=f"[{player.x}, {player.y}, {player.z}]({self.client.url}?x={player.x}&z={player.z}&zoom=10)")
        embed.set_thumbnail(url=self.client.url + player.avatar_path if "." not in player.name else None)

        embed.add_field(name="Town", value=player.current_town.name_formatted if player.current_town else "Wilderness")
        embed.add_field(name="Likely residency", value=f"{likely_residency.name_formatted} ({likely_residency.nation.name_formatted if likely_residency.nation else 'Unknown'})" if likely_residency else "Unknown")
        embed.add_field(name="Online", value=f"{functions.generate_time(player.total_online)} <t:{round(player.last_online.timestamp())}:R>")
        embed.add_field(name="Visited Towns", value=f"{len(player.visited)} (`{(len(player.visited) / len(world.towns)) * 100:,.1f}%`)")

        dc = player.find_discord(self.bot)

        if dc:
            embed.add_field(name="Discord Account", value=f"<@{dc}>")
        
        if len(notable_statistics) > 0:
            embed.add_field(name="Notable Statistics", value="- " + "\n- ".join(notable_statistics), inline=False)

        embed.set_footer(text=f"*Server tracking started {int(world.total_tracked/3600/24)} days ago.")

        view_commands = []

        if player.current_town:
            view_commands.append(commands_view.Command("get town", "Town Info", (player.current_town.name,), button_style=discord.ButtonStyle.primary))
        if likely_residency and likely_residency != player.current_town:
            view_commands.append(commands_view.Command("get town", "Likely Residency Info", (likely_residency.name,), button_style=discord.ButtonStyle.primary))
        view_commands.append(commands_view.Command("history player visited_towns", "Visited Towns", (player.name,)))
        
        c_view = commands_view.CommandsView(self, view_commands)

        await interaction.response.send_message(embed=embed, view=c_view)
    
    @app_commands.command(name="town", description="Get info for a specific town")
    @app_commands.autocomplete(town=autocompletes.town_autocomplete)
    async def _town(self, interaction : discord.Interaction, town : str):

        #print_here

        await interaction.response.defer()

        world : dynmap_w.World = self.client.world
        town : dynmap_w.Town = world.get_town(town.replace(" ", "_"), case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")

        borders = town.borders
        
        file_name = graphs.plot_towns([town], outposts=False)
        graph = discord.File(file_name, filename="town_border.png")

        total_residents = world.total_residents
        total_area = town.area_km
        total_online = town.total_activity

        view_commands = [
            commands_view.Command("history town bank", "Bank History", (town.name,)),
            commands_view.Command("history town visitors", "Visitor History", (town.name,)),
            commands_view.Command("history town residents", "Resident History", (town.name,)),
            commands_view.Command("get player", "Mayor Info", (town.ruler,), discord.ButtonStyle.primary, 2)
        ]
        if town.nation and str(town.nation.name.replace(" ", "")) != "":
            view_commands.append(commands_view.Command("get nation", "Nation Info", (town.nation.name,), discord.ButtonStyle.primary, 2))
        
        c_view = commands_view.CommandsView(self, view_commands)

        button = discord.ui.Button(label="View Outposts", emoji="🗺️", row=2)
        def outposts_button(town : dynmap_w.Town, view : discord.ui.View):
            async def outposts_button_callback(interaction : discord.Interaction):
                for item in view.children:
                    if item.label == "View Outposts":
                        item.disabled = True 
                
                file_name = graphs.plot_towns([town], outposts=True)
                graph = discord.File(file_name, filename="town_border_outposts.png")

                interaction.message.embeds[0].set_thumbnail(url=None)
                interaction.message.embeds[0].set_image(url="attachment://town_border_outposts.png")
                
                await interaction.response.edit_message(view=view, attachments=[graph], embed=interaction.message.embeds[0])
            return outposts_button_callback

        button.callback = outposts_button(town, c_view)
        
        if len(town.points) > 1:
            c_view.add_item(button)
        
        notable_statistics = town.get_notable_statistics()

        embed = discord.Embed(
            title=f"Town: {town.name.replace('_', ' ')}", 
            description=f"**{town.name.replace('_', ' ')}** is a town in the {town.describe()} of the world. It has **{town.total_residents}** resident{'' if town.total_residents == 1 else 's'}.",
            color=s.embed
        )
        embed.add_field(name="Nation", value=town.nation.name_formatted if town.nation else "None")
        embed.add_field(name="Type", value=str(town.icon).title() if str(town.icon).replace(" ", "") != "" else "Unknown")
        embed.add_field(name="Daily Tax", value=f"{town.daily_tax}%")
        embed.add_field(name="Bank", value=f"${town.bank:,}")
        embed.add_field(name="Ruler", value=f"{town.ruler}" if str(town.ruler).replace(" ", "") != "" else "Unknown")
        embed.add_field(name="Coordinates", value=f"[{town.x:,d}, {town.y:,d}, {town.z:,d}]({self.client.url}?x={town.x}&z={town.z}&zoom=10)")
        embed.add_field(name="Total Residents", value=f"{town.total_residents} (`{(town.total_residents/total_residents)*100:.1f}%`)")
        embed.add_field(name="Area", value=f"{total_area:,.1f}km² ({round((total_area*(1000^2))/256):,d} plots)")
        embed.add_field(name="Activity", value=f"`{functions.generate_time(total_online)}` <t:{round(town.last_activity.timestamp())}:R>")
        embed.add_field(name="Founded", value=f"{town.founded.strftime('%b %d %Y')} ({town.age} days ago)")
        embed.add_field(name="Public", value=str(town.public))
        embed.add_field(name="Population Density", value=f"{round(((total_area/town.total_residents)*(1000^2))/256):,d} plots/resident")

        if town.culture:
            embed.add_field(name="Culture", value=town.culture.name)
        if town.religion:
            embed.add_field(name="Religion", value=town.religion.name)
        
        if len(borders) > 0:
            embed.add_field(name=f"Borders ({len(town.borders)})", value="`" + "`, `".join(t.name_formatted for t in borders) + "`", inline=False)
        
        if len(notable_statistics) > 0:
            embed.add_field(name="Notable Statistics", value="- " + "\n- ".join(notable_statistics), inline=False)

        embed.set_thumbnail(url="attachment://town_border.png")

        await interaction.followup.send(embed=embed, file=graph, view=c_view)
    
    async def _nation_pie_res(self, command_cog, interaction : discord.Interaction, nation : dynmap_w.Nation, *args):
        towns = list(sorted(nation.towns, key=lambda x: x.total_residents, reverse=True))

        description_string = ""
        plottable = {}
        for i, town in enumerate(towns):
            plottable[town.name_formatted] = town.total_residents
            description_string += f"{i+1}. {town.name_formatted}: `{town.total_residents}` ({(town.total_residents/nation.total_residents)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        file_name = graphs.save_graph(
            plottable, 
            "", 
            "", 
            "", 
            pie
        )
        
        graph = discord.File(file_name, filename="pie_chart.png")
    
        embed = discord.Embed(title=f"{nation.name_formatted} towns by residents ({len(towns)})", color=s.embed)
        embed.set_image(url="attachment://pie_chart.png")
        view = paginator.PaginatorView(embed, description_string)

        await interaction.response.send_message(file=graph, embed=embed, view=view)
    
    async def _nation_pie_area(self, command_cog, interaction : discord.Interaction, nation : dynmap_w.Nation, *args):
        towns = list(sorted(nation.towns, key=lambda x: x.area_km, reverse=True))

        description_string = ""
        plottable = {}
        nation_area = nation.area_km
        for i, town in enumerate(towns):
            town_area = town.area_km
            plottable[town.name_formatted] = (town_area*(1000^2))/256
            description_string += f"{i+1}. {town.name_formatted}: `{(town_area*(1000^2))/256:,.0f} plots` ({town_area:,.2f}km²) ({(town_area/nation_area)*100:,.2f}%)\n"

        plottable = dict(graphs.take(25, plottable.items()))

        file_name = graphs.save_graph(
            plottable, 
            "", 
            "", 
            "", 
            pie
        )
        
        graph = discord.File(file_name, filename="pie_chart.png")
    
        embed = discord.Embed(title=f"{nation.name_formatted} towns by size ({len(towns)})", color=s.embed)
        embed.set_image(url="attachment://pie_chart.png")
        view = paginator.PaginatorView(embed, description_string)

        await interaction.response.send_message(file=graph, embed=embed, view=view)


    @app_commands.command(name="nation", description="Get info for a specific nation")
    @app_commands.autocomplete(nation=autocompletes.nation_autocomplete)
    async def _nation(self, interaction : discord.Interaction, nation : str):

        #print_here

        await interaction.response.defer()

        world : dynmap_w.World = self.client.world
        nation : dynmap_w.Nation = world.get_nation(nation.replace(" ", "_"), case_sensitive=False)

        if not nation:
            raise e.MildError("Nation not found")

        towns = list(sorted(nation.towns, key=lambda x: x.total_residents, reverse=True))
        notable_statistics = nation.get_notable_statistics(50)

        borders = nation.borders

        file_name = graphs.plot_towns(towns, plot_spawn=False)
        graph = discord.File(file_name, filename="nation_towns.png")

        total_area = 0
        for town in towns:
            total_area += town.area_km

        embed = discord.Embed(
            title=f"Nation: {nation.name.replace('_', ' ')}",
            color=s.embed
        )

        total_residents = nation.total_residents

        embed.add_field(name="Residents", value=str(nation.total_residents))
        embed.add_field(name="Capital", value=nation.capital.name_formatted)
        embed.add_field(name="Leader", value=nation.capital.ruler)
        embed.add_field(name="Area", value=f"{total_area:,.1f}km² ({round((total_area*(1000^2))/256):,d} plots)")
        embed.add_field(name="Population Density", value=f"{round(((total_area/total_residents)*(1000^2))/256):,d} plots/resident")
        embed.add_field(name=f"Towns ({len(towns)})", value="`" + "`, `".join([t.name for t in towns]) + "`", inline=False)

        culture_make_up = nation.culture_make_up
        if len(culture_make_up) > 0:
            embed.add_field(name="Culture Make Up", value="- " + "\n- ".join([f"{name}: {(residents/total_residents)*100:,.2f}%" for name, residents in nation.culture_make_up.items()][:5]))
        religion_make_up = nation.religion_make_up
        if len(religion_make_up) > 0:
            embed.add_field(name="Religion Make Up", value="- " + "\n- ".join([f"{name}: {(residents/total_residents)*100:,.2f}%" for name, residents in nation.religion_make_up.items()][:5]))

        if len(borders) > 0:
            embed.add_field(name=f"Borders ({len(nation.borders)})", value="`" + "`, `".join(t.name_formatted for t in borders) + "`", inline=False)

        if len(notable_statistics) > 0:
            embed.add_field(name="Notable Statistics", value="- " + "\n- ".join(notable_statistics), inline=False)

        embed.set_thumbnail(url="attachment://nation_towns.png")

        view_commands = [
            commands_view.Command("get player", "Leader Info", (nation.capital.ruler,)),
        ]
        if len(nation.towns) > 1:
            view_commands.append(commands_view.Command(self._nation_pie_res, "Town residents pie chart", (nation,), discord.ButtonStyle.primary))
            view_commands.append(commands_view.Command(self._nation_pie_area, "Town area pie chart", (nation,), discord.ButtonStyle.primary))
        
        c_view = commands_view.CommandsView(self, view_commands)
        c_view.add_item(towns_view.SelectTowns(self, self.bot.tree, towns[:25]))

        await interaction.followup.send(embed=embed, view=c_view, file=graph)
    
    @app_commands.command(name="culture", description="Get info for a culture")
    @app_commands.autocomplete(culture=autocompletes.culture_autocomplete)
    async def _culture(self, interaction : discord.Interaction, culture : str):
        await interaction.response.defer()

        world : dynmap_w.World = self.client.world
        culture : dynmap_w.Culture = world.get_culture(culture, case_sensitive=False)

        if not culture:
            raise e.MildError("Culture not found")

        towns = list(sorted(culture.towns, key=lambda x: x.total_residents, reverse=True))

        file_name = graphs.plot_towns(towns, plot_spawn=False)
        graph = discord.File(file_name, filename="culture_towns.png")

        embed = discord.Embed(
            title=f"Culture: {culture.name}",
            color=s.embed
        )

        embed.add_field(name="Residents", value=str(culture.total_residents))
        embed.add_field(name=f"Towns ({len(towns)})", value="`" + "`, `".join([t.name for t in towns]) + "`", inline=False)

        embed.set_image(url="attachment://culture_towns.png")

        view = discord.ui.View(timeout=3600)
        view.add_item(towns_view.SelectTowns(self, self.bot.tree, towns[:25]))

        await interaction.followup.send(embed=embed, file=graph, view=view)
    
    @app_commands.command(name="religion", description="Get info for a religion")
    @app_commands.autocomplete(religion=autocompletes.religion_autocomplete)
    async def _religion(self, interaction : discord.Interaction, religion : str):
        await interaction.response.defer()

        world : dynmap_w.World = self.client.world
        religion : dynmap_w.Religion = world.get_religion(religion, case_sensitive=False)

        if not religion:
            raise e.MildError("Religion not found")

        towns = list(sorted(religion.towns, key=lambda x: x.total_residents, reverse=True))

        file_name = graphs.plot_towns(towns, plot_spawn=False)
        graph = discord.File(file_name, filename="religion_towns.png")

        embed = discord.Embed(
            title=f"Religion: {religion.name}",
            color=s.embed
        )

        embed.add_field(name="Followers", value=str(religion.total_followers))
        embed.add_field(name=f"Towns ({len(towns)})", value="`" + "`, `".join([t.name for t in towns]) + "`", inline=False)

        embed.set_image(url="attachment://religion_towns.png")

        view = discord.ui.View(timeout=3600)
        view.add_item(towns_view.SelectTowns(self, self.bot.tree, towns[:25]))

        await interaction.followup.send(embed=embed, file=graph, view=view)
    
    @app_commands.command(name="world", description="Get a map and world info")
    async def _world(self, interaction : discord.Interaction):
        
        #print_here

        await interaction.response.defer()
        
        world : dynmap_w.World = self.client.world

        file_name = graphs.plot_world(world)
        graph = discord.File(file_name, filename="world_map.png")

        total_area = 0
        total_town_value = 0
        total_residents = 0

        for town in world.towns:
            total_area += town.area_km
            total_town_value += town.bank
            total_residents += town.total_residents
        

        embed = discord.Embed(title="RulerCraft Earth", color=s.embed)
        embed.set_image(url="attachment://world_map.png")

        embed.add_field(name="Total towns", value=f"{len(world.towns)}")
        embed.add_field(name="Total nations", value=f"{len(world.nations)}")
        embed.add_field(name="Total town value", value=f"${total_town_value:,.2f}")
        embed.add_field(name="Total claimed area", value=f"{total_area:,.1f}km² ({round((total_area*(1000^2))/256):,d} plots)")
        embed.add_field(name="Total residents", value=f"{total_residents:,d} ({len(world.players):,d} known)")
        embed.add_field(name="Total cultures", value=f"{len(world.cultures):,d}")
        embed.add_field(name="Total religions", value=f"{len(world.religions):,d}")

        await interaction.followup.send(embed=embed, file=graph)
    
    @app_commands.command(name="raw", description="Get the raw tracking data in a JSON format")
    async def _raw(self, interaction : discord.Interaction):
        await interaction.response.defer()

        world_dict = json.dumps(self.client.world.to_dict())

        s_world = io.StringIO()
        s_world.write(world_dict)
        s_world.seek(0)
        
        await interaction.followup.send(file=discord.File(fp=s_world, filename="world_data.json"))
    

async def setup(bot : commands.Bot):
    await bot.add_cog(Get(bot, bot.client))



