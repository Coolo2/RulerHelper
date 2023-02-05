import discord 
import os

from discord import app_commands
from discord.ext import commands

import dynmap

import setup as s
from funcs import cmds
from funcs.components import paginator
import typing

class Info(commands.GroupCog, name="info", description="Bot info"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client

        self.cmd_list : typing.List[app_commands.AppCommand] = None
    
    @app_commands.command(name="help", description="Get a list of bot commands with a description of their function")
    async def _help(self, interaction : discord.Interaction):
        cmd_list = self.cmd_list = self.cmd_list or await self.bot.tree.fetch_commands()
        
        #print_here

        embed = discord.Embed(title="Ruler Help", color=s.embed)
        content = ""

        # Home
        for full_cmd in cmd_list:
            content += f"\n**/{full_cmd.name}**\n"
            for sub_command in full_cmd.options:
                if type(sub_command) == app_commands.models.Argument:
                    continue
                content += f"- </{full_cmd.name} {sub_command.name}:{full_cmd.id}>\n"
                for sub_sub_command in sub_command.options:
                    if type(sub_sub_command) == app_commands.models.Argument:
                        continue
                    content += f"•  </{full_cmd.name} {sub_command.name} {sub_sub_command.name}:{full_cmd.id}>\n"

        content += "newpage"
        for full_cmd in cmd_list:
            content += f"\n/{full_cmd.name}\n"
            for sub_command_name, sub_command in cmds.dict[full_cmd.name].items():
                content += f"\n- </{full_cmd.name} {sub_command_name}:{full_cmd.id}>"
                if type(sub_command) == dict:
                    for sub_sub_command_name, sub_sub_command in sub_command.items():
                        content += f"\n• </{full_cmd.name} {sub_command_name} {sub_sub_command_name}:{full_cmd.id}> - {sub_sub_command[0]}"
                else:
                    content += f" - {sub_command[0]}"
            
            content += "newpage"

        view = paginator.PaginatorView(embed, content, "newpage", 1)
        await interaction.response.send_message(embed=view.embed, view=view)
    
    @app_commands.command(name="info", description="Get basic info and stats about the bot")
    async def _info(self, interaction : discord.Interaction):
        #print_here
        tracking = self.client.get_tracking()
        
        embed = discord.Embed(title="Bot information", description="Ruler Helper is a bot created by <@368071242189897728> to provide some helpful tools to nations and towns.", color=s.embed)

        embed.add_field(name="Tracking time", value=f"{int(tracking.total_tracked_seconds/3600/24)}d")
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Database size", value=f"{round(os.path.getsize('rulercraft/server_data.pickle')/1000/1000, 2)}MB")
        embed.add_field(name="Last refresh", value=f"<t:{round(tracking.last.timestamp())}:R>")

        total_linked_accounts = 0

        for player in tracking.players:
            if player.find_discord():
                total_linked_accounts += 1
        
        embed.add_field(name="Linked Discord accounts", value=str(total_linked_accounts))

        await interaction.response.send_message(embed=embed)


async def setup(bot : commands.Bot):
    await bot.add_cog(Info(bot, bot.client))