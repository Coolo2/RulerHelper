

from discord.ext import commands 
import discord
import os
import aiohttp

async def reaction_event(bot : commands.Bot, payload : discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    message : discord.Message = await (bot.get_channel(payload.channel_id)).fetch_message(payload.message_id)
    if len(message.embeds) > 0 and "Poll from" in message.embeds[0].title:
        embed = message.embeds[0]

        embed.clear_fields()

        for_reactions = []
        against_reactions = []
        remove = []

        for reaction in message.reactions:
            async for user in reaction.users():
                if user.id == bot.user.id:
                    continue 

                if reaction.emoji == "✅":
                    for_reactions.append(user)
                if type(reaction.emoji) != str and reaction.emoji.id == 952490666192162826:
                    against_reactions.append(user)
        
        for user in for_reactions:
            if user in against_reactions:
                remove.append(user)
        
        for user in remove:
            for_reactions.remove(user)
            against_reactions.remove(user)
        
        if len(against_reactions) == 0 and len(for_reactions) == 0:
            for_percent = 0
        elif len(against_reactions) == 0:
            for_percent = 100
        else:
            for_percent = round((len(for_reactions) / (len(against_reactions) + len(for_reactions))) * 100)


        embed.add_field(name="Stats", value=f"""
For: **{len(for_reactions)}**
Against: **{len(against_reactions)}**
For%: **{for_percent}%**
        """)

        await message.edit(embed=embed)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload : discord.RawReactionActionEvent):
        await reaction_event(self.bot, payload)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload : discord.RawReactionActionEvent):
        await reaction_event(self.bot, payload)
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild):
        
        webhook = discord.Webhook.from_url(os.getenv("webhook"), session=aiohttp.ClientSession())

        await webhook.send(f"New server: `{guild.name}`")
        

async def setup(bot):
    await bot.add_cog(Events(bot))