
import discord 
from discord import app_commands

from discord.ext import commands

import setup as s
import dynmap

class Poll(commands.GroupCog, name="poll", description="All poll commands"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client

        super().__init__()

    
    @app_commands.command(name="poll", description="A simple yes/no poll")
    async def _poll(self, interaction : discord.Interaction, question : str):

        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")

        embed = discord.Embed(title=f"Poll from {interaction.user}", description=f'*{question}*', color=s.embed)
        embed.add_field(name="Stats", value="For: **0**\nAgainst: **0**\nFor%: **0%**")

        await interaction.response.send_message(embed=embed)

        msg = await interaction.original_message()

        await msg.add_reaction("✅")
        await msg.add_reaction("<:cross:952490666192162826>")
    
    @app_commands.command(name='question', description="Create a multiple choice question")
    async def question(
        self, 
        interaction : discord.Interaction,
        question : str,
        choice1 : str,
        choice2 : str,
        choice3 : str = None,
        choice4 : str = None,
        choice5 : str = None,
        choice6 : str = None,
        choice7 : str = None,
        choice8 : str = None,
        choice9 : str = None,
        choice10 : str = None,
    ):
        print(f"{interaction.user} {interaction.guild.name if interaction.guild else ''} #{interaction.channel.name if hasattr(interaction.channel, 'name') else ''} {interaction.command.name} {interaction.expires_at}")
        
        choices = [choice1, choice2, choice3, choice4, choice5, choice6, choice7, choice8, choice9, choice10]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        choices = [x for x in choices if x is not None]

        embed = discord.Embed(title=f"Question from {interaction.user}", description=question, colour=s.embed)

        index = 0
        for choice in choices:
            index += 1
            try:
                embed.add_field(name=f"Option {index}", value=choice)
            except Exception as e:
                pass

                
        await interaction.response.send_message(embed=embed)

        msg = await interaction.original_message()
        
        for i in range(len(choices)):
            await msg.add_reaction(emojis[i])

async def setup(bot : commands.Bot):
    await bot.add_cog(Poll(bot, bot.client))



