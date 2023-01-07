import discord 
import json

from discord import app_commands
from discord.ext import commands

import dynmap

import setup as s
from dynmap import errors as e

import typing

Choice = app_commands.Choice

notification_settings = {
    "territory_enter":["ignore_if_resident"]
}

@app_commands.default_permissions(manage_guild=True)
class Notifications(commands.GroupCog, name="notifications", description="Setup nation notifications in a channel in your server"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client
    
    @app_commands.command(name="enable", description="Enable notifications in a specific channel")
    @app_commands.choices(notification_type=[Choice(name=n.replace("_", " ").title(), value=n) for n in notification_settings.keys()])
    async def _enable(self, interaction : discord.Interaction, notification_type : str, channel : discord.TextChannel, nation : str):
        world = self.client.cached_worlds["RulerEarth"]
        n = world.get_nation(nation.replace(" ", "_"), case_sensitive=False)

        if not n:
            raise e.MildError("Nation does not exist!")

        with open("rulercraft/config.json") as f:
            global_config = json.load(f)
        
        if "notifications" not in global_config:
            global_config["notifications"] = {}
        
        global_config["notifications"][str(channel.id)] = {}
        global_config["notifications"][str(channel.id)][notification_type] = True 
        global_config["notifications"][str(channel.id)]["nation"] = n.name 

        with open("rulercraft/config.json", "w") as f:
            json.dump(global_config, f, indent=4)
        
        try:
            await channel.send("> Notifications have been enabled in this channel. See config with `/notifications config view`")
        except:
            return await interaction.response.send_message(discord.Embed(title="Partially enabled", description="Enabled in this channel, however I don't seem to have access to send messages. Please give me access to send messages there!"))
        embed=discord.Embed(title="Successfully enabled", description=f"Successfully enabled notifications in {channel.mention}", color=s.embedSuccess)
        embed.set_footer(text="Notifications refresh every 20 seconds")
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="disable", description="Disable notifications in a specific channel")
    async def _disable(self, interaction : discord.Interaction, channel : discord.TextChannel):
        with open("rulercraft/config.json") as f:
            global_config = json.load(f)
        
        if "notifications" not in global_config or str(channel.id) not in global_config["notifications"]:
            raise e.MildError("This channel does not have notifications set up! Use `/notifications enable` to enable them.")
        
        del global_config["notifications"][str(channel.id)]

        with open("rulercraft/config.json", "w") as f:
            json.dump(global_config, f, indent=4)
        
        await interaction.response.send_message(embed=discord.Embed(title="Successfully disabled", description=f"Successfully disabled notifications in {channel.mention}", color=s.embedSuccess))
        try:
            await channel.send("> Notifications have been disabled in this channel.")
        except:
            pass
    
    config = app_commands.Group(name="config", description="Notifications config")

    async def get_config_embed(self, global_config : dict, channel : discord.TextChannel) -> discord.Embed:
        config = global_config["notifications"][str(channel.id)]
        local_notification_types = []
        local_notification_settings = []

        # Add settings and types
        for n in notification_settings.keys():
            if n in config:
                local_notification_types.append(n.replace("_", " ").title())

                for setting in notification_settings[n]:
                    if setting in config:
                        local_notification_settings.append(setting.replace("_", " ").title())

        embed = discord.Embed(title=f"Notifications config for #{channel.name}", color=s.embed)
        embed.add_field(name="Nation", value=config["nation"], inline=False)
        embed.add_field(name=f"Enabled notification types", value=", ".join(local_notification_types), inline=False)
        if local_notification_settings != []:
            embed.add_field(name="Enabled notification settings", value=", ".join(local_notification_settings), inline=False)
        else:
            embed.add_field(name="Enabled notification settings", value="None. Set them with `/notifications config set`", inline=False)
        
        return embed

    @config.command(name="view", description="View the config for a channel")
    async def _config_view(self, interaction : discord.Interaction, channel : discord.TextChannel):
        with open("rulercraft/config.json") as f:
            global_config = json.load(f)
        
        if "notifications" not in global_config or str(channel.id) not in global_config["notifications"]:
            return await interaction.response.send_message("This channel does not have notifications set up! Use `/notifications enable` to enable them.")

        await interaction.response.send_message(embed=await self.get_config_embed(global_config, channel))
    
    @config.command(name="set", description="Set configuration for a notification channel")
    async def _config_set(
        self, 
        interaction : discord.Interaction, 
        channel : discord.TextChannel,
        nation : str = None,
        enable_setting : str = None,
        disable_setting : str = None
    ):
        with open("rulercraft/config.json") as f:
            global_config = json.load(f)

        if "notifications" not in global_config or str(channel.id) not in global_config["notifications"]:
            return await interaction.response.send_message("This channel does not have notifications set up! Use `/notifications enable` to enable them.")
        
        config = global_config["notifications"][str(channel.id)]
        changed = False
        
        if nation:
            world = self.client.cached_worlds["RulerEarth"]
            n = world.get_nation(nation.replace(" ", "_"), case_sensitive=False)

            if not n:
                raise e.MildError("Nation does not exist!")
        
            config["nation"] = n.name

            changed = True
        if enable_setting:
            for notification_type, notification_type_settings in notification_settings.items():
                if enable_setting in notification_type_settings:
                    config[enable_setting] = True
            
            changed = True
        if disable_setting:
            if disable_setting in config:
                for notification_type, notification_type_settings in notification_settings.items():
                    if disable_setting in notification_type_settings:
                        del config[disable_setting]
            
            changed = True
        
        if not changed:
            embed = discord.Embed(title="Notification configuration help", color=s.embed)
            embed.add_field(name="Change nation", value="/notifications config set channel={channel} nation={nation_name}", inline=False)
            embed.add_field(name="Enable setting", value="/notifications config set channel={channel} enable_setting={setting}", inline=False)
            embed.add_field(name="Disable setting", value="/notifications config set channel={channel} disable_setting={setting}", inline=False)

            return await interaction.response.send_message(embed=embed)

        embed = await self.get_config_embed(global_config, channel)
        embed.title = f"Successfully set notification config for #{channel.name}"
        embed.color = s.embedSuccess

        await interaction.response.send_message(embed=embed)

        with open("rulercraft/config.json", "w") as f:
            json.dump(global_config, f, indent=4)

    
    @_enable.autocomplete("nation")
    async def _nation_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=m.name_formatted, value=m.name_formatted)
            for m in self.client.cached_worlds["RulerEarth"].nations if current.lower().replace("_", " ") in m.name_formatted.lower()
        ][:25]
    
    @_config_set.autocomplete("nation")
    async def _nation_autocomplete(self, interaction : discord.Interaction, current : str):
        return [
            app_commands.Choice(name=m.name_formatted, value=m.name_formatted)
            for m in self.client.cached_worlds["RulerEarth"].nations if current.lower().replace("_", " ") in m.name_formatted.lower()
        ][:25]
    
    @_config_set.autocomplete("enable_setting")
    async def _enable_setting_autocomplete(self, interaction : discord.Interaction, current : str):
        channel = interaction.client.get_channel(interaction.namespace.__dict__["channel"].id)

        with open("rulercraft/config.json") as f:
            global_config = json.load(f)
        
        config = global_config["notifications"][str(channel.id)] if "notifications" in global_config and str(channel.id) in global_config["notifications"] else {}
        if config == {}:
            return [app_commands.Choice(name="This channel does not have notifications setup. Please use /notifications enable first.", value="None")]
        
        resp = []
        
        for n in notification_settings.keys():
            if n in config:
                for setting in notification_settings[n]:
                    if setting not in config:
                        resp.append(app_commands.Choice(name=setting.replace("_", " ").title(), value=setting))

        return resp[:25]
    
    @_config_set.autocomplete("disable_setting")
    async def _disable_setting_autocomplete(self, interaction : discord.Interaction, current : str):
        channel = interaction.client.get_channel(interaction.namespace.__dict__["channel"].id)

        with open("rulercraft/config.json") as f:
            global_config = json.load(f)
        
        config = global_config["notifications"][str(channel.id)] if "notifications" in global_config and str(channel.id) in global_config["notifications"] else {}
        if config == {}:
            return [app_commands.Choice(name="This channel does not have notifications setup. Please use /notifications enable first.", value="None")]
        
        resp = []
        
        for n in notification_settings.keys():
            if n in config:
                for setting in notification_settings[n]:
                    if setting in config:
                        resp.append(app_commands.Choice(name=setting.replace("_", " ").title(), value=setting))

        return resp[:25]


async def setup(bot : commands.Bot):
    await bot.add_cog(Notifications(bot, bot.client))