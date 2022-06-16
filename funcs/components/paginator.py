import discord

class PaginatorView(discord.ui.View):

    def __init__(self, pages : list, embed : discord.Embed):
        self.embed = embed
        self.pages = pages 
        self.index = 0

        if self.embed.footer.text and "Page " not in self.embed.footer.text:
            self.embed.set_footer(text=f"{self.embed.footer.text} - Page {self.index+1}/{len(self.pages)}")
        else:
            self.embed.set_footer(text=f"Page {self.index+1}/{len(self.pages)}")

        super().__init__()

        self.children[1].disabled = self.index >= len(self.pages) - 1
        self.children[0].disabled = self.index <= 0

        
    
    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="◀️", disabled=True)
    async def _left(self, interaction : discord.Interaction, button: discord.ui.Button):
        embed = self.embed 

        self.index -= 1
        embed.description = self.pages[self.index]

        self.children[1].disabled = self.index >= len(self.pages) - 1
        self.children[0].disabled = self.index <= 0

        embed.set_footer(text=embed.footer.text.replace(f"Page {self.index+2}", f"Page {self.index+1}"))

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="▶️")
    async def _right(self, interaction : discord.Interaction, button: discord.ui.Button):
        
        embed = self.embed 

        self.index += 1
        embed.description = self.pages[self.index]

        self.children[1].disabled = self.index >= len(self.pages) - 1
        self.children[0].disabled = self.index <= 0

        embed.set_footer(text=embed.footer.text.replace(f"Page {self.index}", f"Page {self.index+1}"))
            
        await interaction.response.edit_message(embed=embed, view=self)