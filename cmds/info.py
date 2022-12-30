import discord 
import os

from discord import app_commands
from discord.ext import commands

import dynmap

import setup as s
from funcs import cmds

class Info(commands.GroupCog, name="info", description="Bot info"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client
    
    @app_commands.command(name="help", description="Get a list of bot commands with a description of their function")
    async def _help(self, interaction : discord.Interaction):

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")

        embed = discord.Embed(title="Ruler Help", description="Ruler Helper is a Discord Bot for everything RulerCraft. See its commands below.", color=s.embed)

        for full_cmd_name, full_cmd in cmds.dict.items():
            if type(full_cmd) == dict:
                desc_for_field = ""

                for sub_command_name, sub_command in full_cmd.items():
                    if type(sub_command) == dict:
                        for sub_sub_command_name, sub_sub_command in sub_command.items():
                            desc_for_field += f"**/{full_cmd_name} {sub_command_name} {sub_sub_command_name} {sub_sub_command[1] if len(sub_sub_command) > 1 else ''}** - {sub_sub_command[0]}\n"
                    else:
                        desc_for_field += f"**/{full_cmd_name} {sub_command_name} {sub_command[1] if len(sub_command) > 1 else ''}** - {sub_command[0]}\n"
                
                embed.add_field(name=f"/{full_cmd_name}", value=desc_for_field, inline=False)
            else:
                embed.add_field(name=f"/{full_cmd_name} {full_cmd[1] if len(full_cmd) > 1 else ''}", value=full_cmd[0], inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="info", description="Get basic info and stats about the bot")
    async def _info(self, interaction : discord.Interaction):

        

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")
            

        tracking = self.client.get_tracking()
        
        embed = discord.Embed(title="Bot information", description="Ruler Helper is a bot created by <@368071242189897728> to provide some helpful tools to nations and towns.", color=s.embed)

        embed.add_field(name="Tracking time", value=f"{round(tracking.total_tracked_seconds/3600/24)}d")
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Database size", value=f"{round(os.path.getsize('rulercraft/server_data.pickle')/1000/1000, 2)}MB")

        total_linked_accounts = 0

        for player in tracking.players:
            if player.find_discord():
                total_linked_accounts += 1
        
        embed.add_field(name="Linked Discord accounts", value=str(total_linked_accounts))

        await interaction.response.send_message(embed=embed)


async def setup(bot : commands.Bot):
    await bot.add_cog(Info(bot, bot.client))