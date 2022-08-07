
import discord 

from discord import app_commands
from discord.ext import commands

import dynmap
from dynmap import errors as e

import setup as s

import json

class AcceptView(discord.ui.View):

    def __init__(self, client : dynmap.Client, accept_type, player : str, town : str = None, discord_id : str = None):

        self.client = client

        self.accept_type = accept_type
        self.player = player 
        self.town = town 
        self.discord_id = discord_id 

        self.timeout = None

        super().__init__()
    
    @discord.ui.button(style=discord.ButtonStyle.green, label="Accept")
    async def _accept_button(self, interaction : discord.Interaction, button : discord.ui.Button):
        

        if interaction.user.id not in s.mods:
            raise e.MildError("You are not a Bot Moderator!")

        tracking = self.client.get_tracking()
        tracking_player = tracking.get_player(self.player)
        
        if not tracking_player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")
        
        if self.town != None:
            tracking_town = tracking.get_town(self.town.replace(" ", "_"), case_sensitive=False)
            if not tracking_town:
                raise e.MildError("Town does not exist.")

        if self.accept_type == "likely_residency":
            with open("rulercraft/server_data.json") as f:
                server = json.load(f)

            if tracking_player.name not in server["players"]:
                server["players"][tracking_player.name] = {}
            
            if self.town:
                server["players"][tracking_player.name]["likely_residency"] = tracking_town.town.name
            else:
                if "likely_residency" in server["players"][tracking_player.name]:
                    del server["players"][tracking_player.name]["likely_residency"]
            
            with open("rulercraft/server_data.json", "w") as f:
                json.dump(server, f)
            
            button.disabled = True
            
            await interaction.response.edit_message(content=f"Accepted likely residency change! **{tracking_player.name}**'s likely residency is now **{self.town}**", view=self)

            
        else:

            with open("rulercraft/server_data.json") as f:
                server = json.load(f)

            if tracking_player.name not in server["players"]:
                server["players"][tracking_player.name] = {}
            
            server["players"][tracking_player.name]["discord_id"] = self.discord_id
            
            with open("rulercraft/server_data.json", "w") as f:
                json.dump(server, f)
            
            button.disabled = True
            
            return await interaction.response.edit_message(content=f"Linked discord! <@{self.discord_id}> is now linked to **{tracking_player.name}**", view=self)



    

class Request(commands.GroupCog, name="request", description="Request something from the Bot Moderators"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client
    
    @app_commands.command(name="likely_residency_change", description="Request the bot moderators to change your likely residency.")
    @app_commands.describe(town="Can be set to 'None' to remove.")
    async def _request_likely_residency_change(self, interaction : discord.Interaction, player : str, town : str):

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")

        if town == "None":
            town = None 

        tracking = self.client.get_tracking()
        tracking_player = tracking.get_player(player)

        if town:
            tracking_town = tracking.get_town(town.replace(" ", "_"), case_sensitive=False)
            if not tracking_town:
                raise e.MildError("Town does not exist.")
        

        if not tracking_player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")
        
        channel : discord.TextChannel = self.bot.get_guild(985589916794765332).get_channel(985590035556479017)

        view = AcceptView(self.client, "likely_residency", player, town)

        await channel.send(
            f"/mod set likely_residency {player} {tracking_town.town.name if town else ''}",
            embed=discord.Embed(
                title="Likely residency change request", 
                description=f"{interaction.user.mention} has requested for **{player}** likely residency to be set to **{town}**",
                color=s.embed
            ),
            view=view
        )

        await interaction.response.send_message("Request sent! DM <@368071242189897728> to get more info")

    @_request_likely_residency_change.autocomplete("town")
    async def _residents_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.cached_worlds["RulerEarth"].towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:24] + [app_commands.Choice(name="None", value="None")]
    
    @_request_likely_residency_change.autocomplete("player")
    async def _player_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.get_tracking().players if current.lower() in p.name.lower()
        ][:25]
    
    @app_commands.command(name="discord_link", description="Link Discord and MC name. Allows people to search for your discord name")
    async def _request_discord_link(self, interaction : discord.Interaction, minecraft_name : str):

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")

        tracking_player = self.client.get_tracking().get_player(minecraft_name)
        if not tracking_player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")
        
        channel : discord.TextChannel = self.bot.get_guild(985589916794765332).get_channel(985590035556479017)

        view = AcceptView(self.client, "discord", minecraft_name, discord_id=str(interaction.user.id))

        await channel.send(
            f"/mod set discord {minecraft_name} {interaction.user.id}",
            embed=discord.Embed(
                title="Discord Account link request", 
                description=f"{interaction.user.mention} has requested for their account to be linked to **{minecraft_name}**.",
                color=s.embed
            ),
            view=view
        )

        await interaction.response.send_message("Request sent! DM <@368071242189897728> to get more info")
    
    @_request_discord_link.autocomplete("minecraft_name")
    async def _minecraft_name_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.get_tracking().players if current.lower() in p.name.lower()
        ][:25]
    
# Fix None for likely_residency
# Make view respond

class Mod(commands.Cog):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client
    
    mod = app_commands.Group(name="mod", description="Moderator action commands. Guild only.", default_permissions=discord.Permissions(administrator=True))
    mod_set = app_commands.Group(name="set", description="Set things as a moderator", parent=mod)

    @app_commands.default_permissions(administrator=True)
    @mod_set.command(name="likely_residency", description="Set the likely residency for a user.")
    @app_commands.describe(player="The player to set for", town="The town to set the user's likely residency to. Leave blank to remove")
    async def _set_likely_residency(self, interaction : discord.Interaction, player : str, town : str = None):

        if interaction.user.id not in s.mods:
            raise e.MildError("You are not a Bot Moderator!")
        
        tracking = self.client.get_tracking()
        tracking_player = tracking.get_player(player)

        if town != None:
            tracking_town = tracking.get_town(town.replace(" ", "_"), case_sensitive=False)
            if not tracking_town:
                raise e.MildError("Town does not exist.")

        if not tracking_player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")
        
        with open("rulercraft/server_data.json") as f:
            server = json.load(f)

        if player not in server["players"]:
            server["players"][player] = {}
        
        if town:
            server["players"][player]["likely_residency"] = tracking_town.town.name
        else:
            if "likely_residency" in server["players"][player]:
                del server["players"][player]["likely_residency"]
        
        with open("rulercraft/server_data.json", "w") as f:
            json.dump(server, f)
        
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="Successfully set likely residency",
                description=f"Successfully set the likely residency for **{player}** to **{town}**.",
                color=s.embedSuccess
            )
        )

    @_set_likely_residency.autocomplete("town")
    async def _residents_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.cached_worlds["RulerEarth"].towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @_set_likely_residency.autocomplete("player")
    async def _player_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.get_tracking().players if current.lower() in p.name.lower()
        ][:25]
    
    @app_commands.default_permissions(administrator=True)
    @mod_set.command(name="discord", description="Link your discord account to your minecraft profile on the bot.")
    @app_commands.describe(minecraft_name="Your minecraft name to link to")
    async def _link_discord(self, interaction : discord.Interaction, minecraft_name : str, discord_id : str):

        if interaction.user.id not in s.mods:
            raise e.MildError("You are not a Bot Moderator!")

        tracking = self.client.get_tracking()
        tracking_player = tracking.get_player(minecraft_name)

        if not tracking_player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")
        
        with open("rulercraft/server_data.json") as f:
            server = json.load(f)

        if minecraft_name not in server["players"]:
            server["players"][minecraft_name] = {}
        
        server["players"][minecraft_name]["discord_id"] = discord_id
        
        with open("rulercraft/server_data.json", "w") as f:
            json.dump(server, f)
        
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="Successfully linked Discord",
                description=f"Successfully linked discord account <@{discord_id}> to **{minecraft_name}**.",
                color=s.embedSuccess
            )
        )

    @_link_discord.autocomplete("minecraft_name")
    async def _minecraft_name(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.get_tracking().players if current.lower() in p.name.lower()
        ][:25]

async def setup(bot : commands.Bot):
    await bot.add_cog(Request(bot, bot.client))
    await bot.add_cog(Mod(bot, bot.client), guilds=s.slash_guilds)





