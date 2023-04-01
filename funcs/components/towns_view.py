import discord 
from discord import app_commands

class SelectTowns(discord.ui.Select):
    def __init__(self, cog, tree : app_commands.CommandTree, towns):
        super().__init__()

        for town in towns:
            self.add_option(label=town.name)
        
        self.tree = tree
        self.cog = cog

        self.placeholder = "Select a town"

    async def callback(self, interaction : discord.Interaction):
        await self.tree.get_command("get").get_command("town")._callback(self.cog, interaction, self.values[0])