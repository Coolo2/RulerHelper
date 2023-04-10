
import discord 

from discord import app_commands
from discord.ext import commands

import dynmap
from dynmap import errors as e
from dynmap import world as w

import setup as s

import pickle
import aiofiles

class AcceptView(discord.ui.View):

    def __init__(self, client : dynmap.Client, accept_type, player : w.Player, town : w.Town = None, discord_id : str = None):

        self.client = client

        self.accept_type = accept_type
        self.player = player 
        self.town = town 
        self.discord_id = discord_id 

        

        super().__init__()

        self.timeout = None
    
    @discord.ui.button(style=discord.ButtonStyle.green, label="Accept")
    async def _accept_button(self, interaction : discord.Interaction, button : discord.ui.Button):
        

        if interaction.user.id not in s.mods:
            raise e.MildError("You are not a Bot Moderator!")
        

        if self.accept_type == "likely_residency":
            
            if self.town:
                self.player.likely_residency_set = self.town.name
            else:
                self.player.likely_residency_set = None
            
            async with aiofiles.open('rulercraft/server_data.pickle', 'wb') as f:
                await f.write(pickle.dumps(self.client.world.to_dict()))
            
            button.disabled = True
            
            await interaction.response.edit_message(content=f"Accepted likely residency change! **{self.player.name}**'s likely residency is now **{self.town.name_formatted}**", view=self)

            
        else:
            
            self.player.discord_id_set = self.discord_id
            
            async with aiofiles.open('rulercraft/server_data.pickle', 'wb') as f:
                await f.write(pickle.dumps(self.client.world.to_dict()))
            
            button.disabled = True
            
            return await interaction.response.edit_message(content=f"Linked discord! <@{self.discord_id}> is now linked to **{self.player.name}**", view=self)



    

class Request(commands.GroupCog, name="request", description="Request something from the Bot Moderators"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client
    
    @app_commands.command(name="likely_residency_change", description="Request the bot moderators to change your likely residency.")
    @app_commands.describe(town="Can be set to 'None' to remove.")
    async def _request_likely_residency_change(self, interaction : discord.Interaction, player : str, town : str):

        #print_here

        if town == "None":
            town = None 

        player : w.Player = self.client.world.get_player(player, case_sensitive=False)

        if town:
            town : w.Town = self.client.world.get_town(town.replace(" ", "_"), case_sensitive=False)
            if not town:
                raise e.MildError("Town does not exist.")
        
        if not player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")
        
        channel : discord.TextChannel = self.bot.get_channel(s.mod_notification_channel)

        view = AcceptView(self.client, "likely_residency", player, town)

        await channel.send(
            f"/mod set likely_residency {player.name} {town.name if town else ''}",
            embed=discord.Embed(
                title="Likely residency change request", 
                description=f"{interaction.user.mention} has requested for **{player.name}** likely residency to be set to **{town.name_formatted}**",
                color=s.embed
            ),
            view=view
        )

        await interaction.response.send_message(f"Request sent! DM <@{s.mods[0]}> to get more info")

    @_request_likely_residency_change.autocomplete("town")
    async def _residents_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.world.towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:24] + [app_commands.Choice(name="None", value="None")]
    
    @_request_likely_residency_change.autocomplete("player")
    async def _player_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.world.players if current.lower() in p.name.lower()
        ][:25]
    
    @app_commands.command(name="discord_link", description="Link Discord and MC name. Allows people to search for your discord name")
    async def _request_discord_link(self, interaction : discord.Interaction, minecraft_name : str):

        #print_here

        player = self.client.world.get_player(minecraft_name)
        if not player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")
        
        channel : discord.TextChannel = self.bot.get_channel(s.mod_notification_channel)

        view = AcceptView(self.client, "discord", player, discord_id=str(interaction.user.id))

        await channel.send(
            f"/mod set discord {minecraft_name} {interaction.user.id}",
            embed=discord.Embed(
                title="Discord Account link request", 
                description=f"{interaction.user.mention} has requested for their account to be linked to **{minecraft_name}**.",
                color=s.embed
            ),
            view=view
        )

        await interaction.response.send_message(f"Request sent! DM <@{s.mods[0]}> to get more info")
    
    @_request_discord_link.autocomplete("minecraft_name")
    async def _minecraft_name_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.world.players if current.lower() in p.name.lower()
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
        
        player : w.Player = self.client.world.get_player(player)

        if town != None:
            town : w.Town = self.client.world.get_town(town.replace(" ", "_"), case_sensitive=False)
            if not town:
                raise e.MildError("Town does not exist.")

        if not player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")

        if town:
            player.likely_residency_set = town.name
        else:
            player.likely_residency_set = None
        
        async with aiofiles.open('rulercraft/server_data.pickle', 'wb') as f:
            await f.write(pickle.dumps(self.client.world.to_dict()))
        
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="Successfully set likely residency",
                description=f"Successfully set the likely residency for **{player.name}** to **{town.name_formatted if town else 'None'}**.",
                color=s.embedSuccess
            )
        )

    @_set_likely_residency.autocomplete("town")
    async def _residents_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.world.towns if current.lower().replace("_", " ") in t.name_formatted.lower()
        ][:25]
    
    @_set_likely_residency.autocomplete("player")
    async def _player_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.world.players if current.lower() in p.name.lower()
        ][:25]
    
    @app_commands.default_permissions(administrator=True)
    @mod_set.command(name="discord", description="Link your discord account to your minecraft profile on the bot.")
    @app_commands.describe(minecraft_name="Your minecraft name to link to")
    async def _link_discord(self, interaction : discord.Interaction, minecraft_name : str, discord_id : str):

        if interaction.user.id not in s.mods:
            raise e.MildError("You are not a Bot Moderator!")

        player = self.client.world.get_player(minecraft_name)

        if not player:
            raise e.MildError("Player not found! They have to have joined the server recently to be added.")

        if discord_id == "none":
            player.discord_id_set = None
        else:
            player.discord_id_set = discord_id
        
        async with aiofiles.open('rulercraft/server_data.pickle', 'wb') as f:
            await f.write(pickle.dumps(self.client.world.to_dict()))
        
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
            for p in self.client.world.players if current.lower() in p.name.lower()
        ][:25]

async def setup(bot : commands.Bot):
    await bot.add_cog(Request(bot, bot.client))
    await bot.add_cog(Mod(bot, bot.client), guilds=s.slash_guilds)





