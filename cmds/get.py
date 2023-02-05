
import discord 
import json
import io

from discord import app_commands
from discord.ext import commands

import dynmap
from dynmap import world as dynmap_w 
from dynmap import tracking as dynmap_t

from funcs.components import paginator, commands_view
import setup as s

from dynmap import errors as e

from funcs import functions, graphs, autocompletes

class Get(commands.GroupCog, name="get", description="All get commands"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client

        super().__init__()

    
    @app_commands.command(name="online", description="Get online members and their positions")
    async def _online(self, interaction : discord.Interaction):

        #print_here

        await interaction.response.defer()

        tracking = self.client.get_tracking()

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        embed = discord.Embed(title=f"Online players ({len(world.players)})",
            color=s.embed)
        
        file_name = graphs.plot_world(world, True, tracking)
        graph = discord.File(file_name, filename="world_map.png")

        description_string = ""
        for player in world.players:
            tracking_player : dynmap_t.TrackPlayer = tracking.get_player(player.name)

            description_string += f"**{player.name}**:    [{player.x:,d}, {player.y:,d}, {player.z:,d}]({self.client.url}?x={player.x}&z={player.z}&zoom=8) (`{round((tracking_player.total_online_seconds / tracking_player.tracking.total_tracked_seconds) * 100)}%`)\n"
        
        embed.set_image(url="attachment://world_map.png")

        view = paginator.PaginatorView(embed, description_string)

        await interaction.followup.send(embed=view.embed, view=view, file=graph)
    
    @app_commands.command(name="player", description="Get info for a specific player")
    async def _player(self, interaction : discord.Interaction, player : str):

        #print_here

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        tracking_player : dynmap_t.TrackPlayer = self.client.get_tracking().get_player(player, case_sensitive=False)
        player : dynmap_w.Player = world.get_player(player, case_sensitive=False)

        if not tracking_player:
            raise e.MildError("Player not found")

        embed = discord.Embed(title=f"Player: {tracking_player.name}",
                color=s.embed)

        likely_residency = tracking_player.get_likely_residency()

        if player:
            embed.add_field(name="Health", value=player.health)
            embed.add_field(name="Armour", value=player.armor)
            embed.add_field(name="Coordinates", value=f"[{player.x}, {player.y}, {player.z}]({self.client.url}?x={player.x}&z={player.z}&zoom=10)")

            embed.set_thumbnail(url=player.avatar)
        else:
            embed.description = "*Player is offline, using last seen data.*"

            embed.add_field(name="Coordinates", value=f"[{tracking_player.last_x}, {tracking_player.last_y}, {tracking_player.last_z}]({self.client.url}?x={tracking_player.last_x}&z={tracking_player.last_z}&zoom=10)")

        embed.add_field(name="Town", value=tracking_player.last_town)
        embed.add_field(name="Likely residency", value=f"{likely_residency.town.name_formatted} ({likely_residency.town.nation.name_formatted if likely_residency.town.nation else 'Unknown'})" if likely_residency and likely_residency.town else "Unknown")
        embed.add_field(name="Online", value=f"{functions.generate_time(tracking_player.total_online_seconds)} <t:{round(tracking_player.last_seen_timestamp)}:R>")

        dc = tracking_player.find_discord()

        if dc:
            embed.add_field(name="Discord Account", value=f"<@{dc}>")

        embed.set_footer(text=f"*Server tracking started {int(tracking_player.tracking.total_tracked_seconds/3600/24)} days ago.")

        view_commands = []

        if tracking_player.town:
            view_commands.append(commands_view.Command("get town", "Town Info", (tracking_player.last_town,), button_style=discord.ButtonStyle.primary))
        if tracking_player.town and likely_residency != tracking_player.town.town:
            view_commands.append(commands_view.Command("get town", "Likely Residency Info", (likely_residency.town.name,), button_style=discord.ButtonStyle.primary))
        view_commands.append(commands_view.Command("history player visited_towns", "Visited Towns", (tracking_player.name,)))
        
        c_view = commands_view.CommandsView(self, view_commands)

        await interaction.response.send_message(embed=embed, view=c_view)

    @_player.autocomplete("player")
    async def _player_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.get_tracking().players if current.lower() in p.name.lower()
        ][:25]
    
    @app_commands.command(name="town", description="Get info for a specific town")
    @app_commands.autocomplete(town=autocompletes.town_autocomplete)
    async def _town(self, interaction : discord.Interaction, town : str):

        #print_here

        await interaction.response.defer()

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        town : dynmap_w.Town = world.get_town(town.replace(" ", "_"), case_sensitive=False)
        tracking_town : dynmap_t.TrackTown = self.client.get_tracking().get_town(town.name, case_sensitive=False)

        if not town:
            raise e.MildError("Town not found")
        
        file_name = graphs.plot_towns([town], outposts=False)
        graph = discord.File(file_name, filename="town_border.png")

        total_residents = world.total_residents
        total_area = town.area_km
        total_online = tracking_town.total_activity

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
        embed.add_field(name="Activity", value=f"`{functions.generate_time(total_online)}` <t:{round(tracking_town.last_activity_timestamp)}:R>")
        embed.add_field(name="Founded", value=f"{town.founded.strftime('%b %d %Y')} ({town.age} days ago)")
        embed.add_field(name="Peaceful", value=str(town.peaceful))

        if town.culture:
            embed.add_field(name="Culture", value=town.culture)

        embed.set_thumbnail(url="attachment://town_border.png")

        await interaction.followup.send(embed=embed, file=graph, view=c_view)
    
    @app_commands.command(name="nation", description="Get info for a specific nation")
    async def _nation(self, interaction : discord.Interaction, nation : str):

        #print_here

        await interaction.response.defer()

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        nation : dynmap_w.Nation = world.get_nation(nation.replace(" ", "_"), case_sensitive=False)

        if not nation:
            raise e.MildError("Nation not found")

        towns = nation.towns

        file_name = graphs.plot_towns(towns)
        graph = discord.File(file_name, filename="nation_towns.png")

        total_area = 0
        for town in towns:
            total_area += town.area_km

        embed = discord.Embed(
            title=f"Nation: {nation.name.replace('_', ' ')}",
            color=s.embed
        )

        embed.add_field(name="Residents", value=str(nation.total_residents))
        embed.add_field(name="Capital", value=nation.capital.name_formatted)
        embed.add_field(name="Leader", value=nation.capital.ruler)
        embed.add_field(name=f"Towns ({len(towns)})", value="`" + "`, `".join([t.name for t in towns]) + "`", inline=False)
        embed.add_field(name="Area", value=f"{total_area:,.1f}km² ({round((total_area*(1000^2))/256):,d} plots)", inline=False)

        embed.set_thumbnail(url="attachment://nation_towns.png")

        tree : app_commands.CommandTree = self.bot.tree 

        class SelectNation(discord.ui.Select):
            def __init__(self, cog, tree : app_commands.CommandTree, towns):
                super().__init__()

                for town in towns:
                    self.add_option(label=town.name)
                
                self.tree = tree
                self.cog = cog

                self.placeholder = "Select a town"

            async def callback(self, interaction : discord.Interaction):
                await self.tree.get_command("get").get_command("town")._callback(self.cog, interaction, self.values[0])
        
        view_commands = [
            commands_view.Command("get player", "Leader Info", (nation.capital.ruler,))
        ]
        
        c_view = commands_view.CommandsView(self, view_commands)
        c_view.add_item(SelectNation(self, tree, towns))

        await interaction.followup.send(embed=embed, view=c_view, file=graph)

    @_nation.autocomplete("nation")
    async def _nation_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=m.name_formatted, value=m.name_formatted)
            for m in self.client.cached_worlds["RulerEarth"].nations if current.lower().replace("_", " ") in m.name_formatted.lower()
        ][:25]
    
    @app_commands.command(name="world", description="Get a map and world info")
    async def _world(self, interaction : discord.Interaction):
        
        #print_here

        await interaction.response.defer()
        
        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]
        tracking = self.client.get_tracking()

        file_name = graphs.plot_world(world)
        graph = discord.File(file_name, filename="world_map.png")

        total_area = 0
        total_town_value = 0
        total_residents = 0
        known_players = 0

        for town in world.towns:
            total_area += town.area_km
            total_town_value += town.bank
            total_residents += town.total_residents
        
        for player in tracking.players:
            known_players += 1

        embed = discord.Embed(title="RulerCraft Earth", color=s.embed)
        embed.set_image(url="attachment://world_map.png")

        embed.add_field(name="Total towns", value=f"{len(world.towns)}")
        embed.add_field(name="Total nations", value=f"{len(world.nations)}")
        embed.add_field(name="Total town value", value=f"${total_town_value:,.2f}")
        embed.add_field(name="Total claimed area", value=f"{total_area:,.1f}km² ({round((total_area*(1000^2))/256):,d} plots)")
        embed.add_field(name="Total residents", value=f"{total_residents:,d} ({known_players:,d} known)")

        await interaction.followup.send(embed=embed, file=graph)
    
    @app_commands.command(name="raw", description="Get the raw tracking data in a JSON format")
    async def _raw(self, interaction : discord.Interaction):
        await interaction.response.defer()

        tracking = self.client.get_tracking()
        server = json.dumps(tracking.raw)
        world_dict = json.dumps(self.client.cached_worlds["RulerEarth"].to_dict())

        s_server = io.StringIO()
        s_server.write(server)
        s_server.seek(0)

        s_world = io.StringIO()
        s_world.write(world_dict)
        s_world.seek(0)
        
        await interaction.followup.send(files=[discord.File(fp=s_server, filename="server_data.json"), discord.File(fp=s_world, filename="world_data.json")])
    

async def setup(bot : commands.Bot):
    await bot.add_cog(Get(bot, bot.client))



