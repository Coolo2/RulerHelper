
import discord 
from discord.ext import commands 
from discord import app_commands 

import typing

class Command():
    def __init__(self, command : str, label : str, parameters : tuple, button_style : discord.ButtonStyle = discord.ButtonStyle.secondary, row=1):
        self.command = command 
        self.label = label 
        self.parameters = parameters 
        self.button_style = button_style
        self.row = row
    
    def get_command_class(self, tree : app_commands.CommandTree) -> app_commands.Command:
        command = None 
        
        for item in self.command.split(" "):
            if not command:
                command = tree.get_command(item)
            else:
                command = command.get_command(item)
        return command
    
    
    async def execute(self, cog, interaction : discord.Interaction):
        await (self.get_command_class(interaction.client.tree)).callback(cog, interaction, *self.parameters)

class CommandsView(discord.ui.View):

    def __init__(self, cog, commands : typing.List[Command]):
        super().__init__(timeout=3600)

        for command in commands:
            
            button = discord.ui.Button(style=command.button_style, label=command.label, emoji="💬", row=command.row)

            def command_callback_runner(cmd):
                async def callback(interaction : discord.Interaction):
                    await cmd.execute(cog, interaction)
                return callback

            button.callback = command_callback_runner(command) 

            self.add_item(button)
            

        
    
