
import discord 
import math
import shapely.geometry
from matplotlib.pyplot import bar

from discord import app_commands
from discord.ext import commands

import dynmap
from dynmap import world as dynmap_w 

from funcs.components import paginator
import setup as s

from dynmap import errors as e

from funcs import graphs, autocompletes, functions

class Compare(commands.GroupCog, name="compare", description="Compare statistics between different things"):

    def __init__(self, bot : commands.Bot, client : dynmap.Client):
        self.bot = bot
        self.client = client

        super().__init__()
    
    @app_commands.command(name="towns", description="Compare two towns")
    @app_commands.autocomplete(town_first=autocompletes.town_autocomplete)
    async def _towns(self, interaction : discord.Interaction, town_first : str, town_second : str):

        await interaction.response.defer()

        town_1 : dynmap_w.Town = self.client.world.get_town(town_first.replace(" ", "_"), case_sensitive=False)
        town_2 : dynmap_w.Town = self.client.world.get_town(town_second.replace(" ", "_"), case_sensitive=False)

        towns = [town_1, town_2]

        if not town_1 or not town_2:
            raise e.MildError("One of the towns was not found")
        
        if town_1.name == town_2.name:
            raise e.MildError("Cannot use same town twice")
        
        embed = discord.Embed(title=f"Town Comparison - {town_1.name_formatted} & {town_2.name_formatted}", color=s.embed)
        content = f"__Introduction__\n\nThis is a comparison between the towns **{town_1.name_formatted}** and **{town_2.name_formatted}**. Click through with the arrows below to see the comparison!"

        # Page 2 - Location
        content += "newpage"
        distance = math.sqrt((town_2.x-town_1.x)**2 + (town_2.z-town_1.z)**2)
        further_east = town_1 if town_1.x > town_2.x else town_2 
        further_north = town_1 if town_1.z < town_2.z else town_2
        densities = [town_1.towns_within_range(3000), town_2.towns_within_range(3000)]

        image_generators = [None, None, None]
        image_generators[0] = (graphs.plot_towns, ([town_1, town_2], False, True if distance > 8000 else False, True if distance < 1000 else False))
        image_generators[1] = (graphs.plot_towns, ([town_1, town_2], True, True if distance > 8000 else False, True if distance < 1000 else False))
        image_generators[2] = image_generators[1]

        content += f"__Location__\n\nThese two towns are **{distance:,.0f} blocks** away from each other. **{further_east.name_formatted}** is further east and {f'**{further_north.name_formatted}** is ' if further_east != further_north else ''}further north. "
        
        if len(densities[0]) > len(densities[1]):
            index = 0 
            alt_index = 1
        else:
            index = 1
            alt_index = 0

        percentage_increase = ((len(densities[index]) / len(densities[alt_index])) * 100) - 100
        content += f"**{towns[index].name_formatted}** is in a **{percentage_increase:.0f}%** denser region, with **{len(densities[index])}** towns within 3000 blocks in comparison to **{len(densities[alt_index])}**"

        # Page 3 - Size
        content += "newpage"
        
            # Area
        if town_1.area_km > town_2.area_km:
            index = 0 
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        percentage_increase = ((towns[index].area_km / towns[alt_index].area_km) * 100) - 100
        content += f"__Size__\n\n**{towns[index].name_formatted}** has a greater area than **{towns[alt_index].name_formatted}**. It is **{percentage_increase:,.0f}%** larger at **{towns[index].area_km:,.2f}km² ({(towns[index].area_km*(1000^2))/256:,.0f} plots)** compared to **{towns[alt_index].area_km:,.2f}km² ({(towns[alt_index].area_km*(1000^2))/256:,.0f} plots)**. "

            # Detatched territories
        if len(town_1.points) == len(town_2.points):
            content += f"**{town_1.name_formatted}** has the same amount of detatched territories as **{town_2.name_formatted}**, both having {'none' if len(town_1.points) == 1 else f'**{len(town_1.points)-1}**'}"
        else:
            if len(town_1.points) >= len(town_2.points):
                index = 0 
                alt_index = 1
            else:
                index = 1
                alt_index = 0

            detatched_area_km = 0
            for point_group in towns[index].points:
                poly = shapely.geometry.Polygon(point_group)
                if not poly.contains(shapely.geometry.Point(towns[index].x, towns[index].z)):
                    detatched_area_km += poly.area / (1000^2)
            detatched_area_percentage = (detatched_area_km / towns[index].area_km) * 100

            
            content += f"**{towns[index].name_formatted}** has more detatched territories than {towns[alt_index].name_formatted}, at **{len(towns[index].points)-1}** compared to **{len(towns[alt_index].points)-1}**. Detatched territories make up **{detatched_area_percentage:,.0f}%** of {towns[index].name_formatted}'s claims"
        
        # Page 4 - Activity
        content += "newpage"

        if town_1.total_residents > town_2.total_residents:
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        res = towns[index].total_residents-towns[alt_index].total_residents
        content += f"__Activity__\n\n**{towns[index].name_formatted}** has {'no' if res == 0 else res} more resident{'' if res == 1 else 's'} than {towns[alt_index].name_formatted} with **{towns[index].total_residents} residents**. Additionally, "

        if town_1.total_activity > town_2.total_activity:
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        
        per_resident = [town_1.total_activity / town_1.total_residents, town_2.total_activity / town_2.total_residents]
        perc_increase = f"{((towns[index].total_activity / towns[alt_index].total_activity) * 100) - 100:,.0f}" if towns[alt_index].total_activity != 0 else "infinite"

        content += f"**{towns[index].name_formatted}** has had more activity (**{perc_increase}%** more) than {towns[alt_index].name_formatted}, with a total of `{functions.generate_time(towns[index].total_activity)}` playtime compared to `{functions.generate_time(towns[alt_index].total_activity)}` during the {int(self.client.world.total_tracked/3600/24)} days of server tracking. "
        if town_1.total_residents != 1 or town_2.total_residents != 1:
            content += f"That is `{functions.generate_time(per_resident[index])}` and `{functions.generate_time(per_resident[alt_index])}` per resident for both towns respectively."
        
        plottable = {
            f"{towns[index].name_formatted} \ntotal":towns[index].total_activity/60, 
            f"{towns[index].name_formatted} \nper resident":towns[index].total_activity/60/towns[index].total_residents, 
            f"{towns[alt_index].name_formatted} \ntotal":towns[alt_index].total_activity/60,
            f"{towns[alt_index].name_formatted} \nper resident":towns[alt_index].total_activity/60/towns[alt_index].total_residents, 
        }

        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Activity Comparison: {town_1.name_formatted} & {town_2.name_formatted}", 
                    "Town", 
                    "Activity (minutes)", 
                    bar
                )
            )
        )

        # Page 5 - Economy
        content += "newpage"

            # Economy - Bank Balance
        if town_1.bank > town_2.bank:
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        
        perc = (towns[index].bank / (towns[alt_index].bank + towns[index].bank)) * 100
        content += f"__Economy__\n\nBoth towns sum to a total balance of **${town_1.bank+town_2.bank:,.2f}**, **{towns[index].name_formatted}** making up **{int(perc)}%** of this figure with **${towns[index].bank:,.2f}** compared to **${towns[alt_index].bank:,.2f}** of {towns[alt_index].name_formatted}. "

        plottable = {
            f"{towns[index].name_formatted} \nbank":towns[index].bank, 
            f"{towns[alt_index].name_formatted} \nbank":towns[alt_index].bank,
        }

            # Economy - Taxes
        if town_1.daily_tax == town_2.daily_tax:
            content += f"Both towns have the same tax of **{town_1.daily_tax:,.2f}%**. "
        else:
            if town_1.daily_tax > town_2.daily_tax:
                index = 0
                alt_index = 1
            else:
                index = 1
                alt_index = 0
            
            content += f"**{towns[index].name_formatted}** has a greater tax at **{towns[index].daily_tax:,.2f}%** compared to **{towns[alt_index].daily_tax:,.2f}%**. "

        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Bank Comparison: {town_1.name_formatted} & {town_2.name_formatted}", 
                    "Town", 
                    "Bank balance ($)", 
                    bar
                )
            )
        )

        # Page 6 - Security
        content += "newpage"
        content += "__Security__\n\n"
        
            # Local resources
        content += f"{town_1.name_formatted} has **${town_1.bank:,.0f}** and **{town_1.total_residents} resident{'' if town_1.total_residents == 1 else 's'}**, and {town_2.name_formatted} has **${town_2.bank:,.0f}** and **{town_2.total_residents} resident{'' if town_2.total_residents == 1 else 's'}** which can be used in defense or attack for both. "
        
        plottable = {
            f"{town_1.name_formatted} \nresidents":town_1.total_residents, 
            f"{town_2.name_formatted} \nresidents":town_2.total_residents,
        }
        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Resident Comparison: {town_1.name_formatted} & {town_2.name_formatted}", 
                    "Town", 
                    "Resident count", 
                    bar
                )
            )
        )

            # Nation
        if not town_1.nation and not town_2.nation:
            content += f"Additionally, both towns are not a part of a nation which means they do not benefit from extra security. "
        elif town_1.nation == town_2.nation:
            content += f"Additionally, both towns are a part of the **{town_1.nation.name_formatted}** nation which means they benefit from similar nation security ({town_1.nation.total_residents} extra residents). "
        else:
            if town_2.nation and not town_1.nation  :
                index = 1
                alt_index = 0
            elif (town_1.nation and not town_2.nation) or (town_1.nation.total_residents + len(town_1.nation.towns) ) >= (town_2.nation.total_residents + len(town_2.nation.towns)):
                index = 0
                alt_index = 1
            else:
                index = 1
                alt_index = 0
            
            if towns[0].nation and towns[1].nation:
                perc_better = ((towns[index].nation.total_residents + len(towns[index].nation.towns)) / (towns[alt_index].nation.total_residents + len(towns[alt_index].nation.towns)) * 100) - 100
                content += f"I estimate that **{towns[index].name_formatted}** is in a {perc_better:,.0f}% better nation than {towns[alt_index].name_formatted}, with **{towns[index].nation.total_residents}** residents and **{towns[alt_index].nation.total_residents}** residents respectively. This means that **{towns[index].name_formatted}** benefits from better security and help from other towns. "
            elif towns[0].nation:
                content += f"**{towns[0].name_formatted}** is in a nation, unlike {towns[1].name_formatted}. This means that **{towns[0].name_formatted}** benefits from better security and help from other towns. "
            else:
                content += f"**{towns[1].name_formatted}** is in a nation, unlike {towns[0].name_formatted}. This means that **{towns[1].name_formatted}** benefits from better security and help from other towns. "

        content += f"**{town_1.name_formatted}** was founded on **{town_1.founded.strftime('%b %d %Y')}** and **{town_2.name_formatted}** was founded on **{town_2.founded.strftime('%b %d %Y')}**. "

        view = paginator.PaginatorView(embed, content, "newpage", 1, page_image_generators=image_generators, search=False)
        await interaction.followup.send(embed=view.embed, view=view, file=view.attachment)
    
    @_towns.autocomplete("town_second")
    async def _second_town_autocomplete(self, interaction : discord.Interaction, current : str):
        values = interaction.namespace.__dict__

        return [
            app_commands.Choice(name=t.name_formatted, value=t.name_formatted)
            for t in self.client.world.towns if current.lower().replace("_", " ") in t.name_formatted.lower() and values["town_first"].replace(" ", "_").lower() != t.name_formatted.lower()
        ][:25]
    
    @app_commands.command(name="nations", description="Compare two nations")
    @app_commands.autocomplete(nation_first=autocompletes.nation_autocomplete)
    async def _nations(self, interaction : discord.Interaction, nation_first : str, nation_second : str):
        
        await interaction.response.defer()

        nation_1 = self.client.world.get_nation(nation_first.replace(" ", "_"), case_sensitive=False)
        nation_2 = self.client.world.get_nation(nation_second.replace(" ", "_"), case_sensitive=False)

        nations = [nation_1, nation_2]

        if not nation_1 or not nation_2:
            raise e.MildError("One of the nations was not found")
        
        if nation_1 == nation_2:
            raise e.MildError("Cannot use same nation twice")
        
        embed = discord.Embed(title=f"Nation Comparison - {nation_1.name_formatted} & {nation_2.name_formatted}", color=s.embed)
        content = f"__Introduction__\n\nThis is a comparison between the nations: **{nation_1.name_formatted}** and **{nation_2.name_formatted}**. Click through with the arrows below."

        image_generators = [
            (graphs.plot_towns, (nation_1.towns + nation_2.towns, False, True if len(nation_1.towns) + len(nation_2.towns) > 10 else False, False))
        ]

        # Page 2 
        content += "newpage"

        if nation_1.total_residents > nation_2.total_residents:
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        percentage_increase = ((nations[index].total_residents / nations[alt_index].total_residents) * 100) - 100

        content += f"__People__\n\n**{nations[index].name_formatted}** has **{percentage_increase:,.0f}%** more residents than **{nations[alt_index].name_formatted}** with {nations[index].total_residents} compared to {nations[alt_index].total_residents}. Their residents are spread across {len(nations[index].towns)} towns with an average of {nations[index].total_residents/len(nations[index].towns):,.1f} residents per town (compared to {len(nations[alt_index].towns)} towns - {nations[alt_index].total_residents/len(nations[alt_index].towns):,.1f} residents per town)."

        plottable = {
            f"{nations[index].name_formatted} \nresidents":nations[index].total_residents, 
            f"{nations[index].name_formatted} \nresidents per town":nations[index].total_residents / len(nations[index].towns), 
            f"{nations[alt_index].name_formatted} \nresidents":nations[alt_index].total_residents,
            f"{nations[alt_index].name_formatted} \nresidents per town":nations[alt_index].total_residents / len(nations[alt_index].towns), 
        }
        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Resident Comparison: {nation_1.name_formatted} & {nation_2.name_formatted}", 
                    "Nation", 
                    "Resident count", 
                    bar
                )
            )
        )

        # Page 3 - Activity
        content += "newpage"

        total_activity = [0, 0]

        
        for town in nation_1.towns:
            total_activity[0] += town.total_activity 
        for town in nation_2.towns:
            total_activity[1] += town.total_activity 
        
        if total_activity[0] > total_activity[1]:
            index = 0 
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        
        content += f"__Activity__\n\n**{nations[index].name_formatted}** is more active than {nations[alt_index].name_formatted}, having a total **{functions.generate_time(total_activity[index])}** playtime compared to **{functions.generate_time(total_activity[alt_index])}** during the {int(self.client.world.total_tracked/3600/24)} days of server tracking. "

        plottable = {
            f"{nations[index].name_formatted} \nplaytime":total_activity[index]/60, 
            f"{nations[index].name_formatted} \nplaytime per town":total_activity[index]/60 / len(nations[index].towns), 
            f"{nations[alt_index].name_formatted} \nplaytime":total_activity[alt_index]/60,
            f"{nations[alt_index].name_formatted} \nplaytime per town":total_activity[alt_index]/60 / len(nations[alt_index].towns), 
        }
        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Activity Comparison: {nation_1.name_formatted} & {nation_2.name_formatted}", 
                    "Nation", 
                    "Activity (Minutes)", 
                    bar
                )
            )
        )

        # Page 4 - Economy
        content += "newpage"

        if nation_1.total_bank/len(nation_1.towns) > nation_2.total_bank/len(nation_2.towns):
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        percentage_increase = (((nations[index].total_bank/len(nations[index].towns)) / (nations[alt_index].total_bank/len(nations[alt_index].towns))) * 100) - 100

        content += f"__Economy__\n\nOn average, **{nations[index].name_formatted}** has **{percentage_increase:,.0f}%** more money per town, with an average of **${nations[index].total_bank/len(nations[index].towns):,.2f}** per town bank, compared to ${nations[alt_index].total_bank/len(nations[alt_index].towns):,.2f} for {nations[alt_index].name_formatted}. **{nations[index].name_formatted}** has a total town bank balance of **${nations[index].total_bank:,.2f}**, while **{nations[alt_index].name_formatted}** has a total town bank balance of **${nations[alt_index].total_bank:,.2f}**"
        
        plottable = {
            f"{nations[index].name_formatted} \nTown Bank Total":nations[index].total_bank, 
            f"{nations[index].name_formatted} \nTown Bank Average":nations[index].total_bank / len(nations[index].towns), 
            f"{nations[alt_index].name_formatted} \nTown Bank Total":nations[alt_index].total_bank,
            f"{nations[alt_index].name_formatted} \nTown Bank Average":nations[alt_index].total_bank / len(nations[alt_index].towns), 
        }
        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Bank Comparison: {nation_1.name_formatted} & {nation_2.name_formatted}", 
                    "Nation", 
                    "Balance ($)", 
                    bar
                )
            )
        )

        # Page 5 - Area
        content += "newpage"

        if nation_1.area_km > nation_2.area_km:
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        percentage_increase = ((nations[index].area_km / nations[alt_index].area_km) * 100) - 100

        content += f"**{nations[index].name_formatted}** is larger than **{nations[alt_index].name_formatted}**, at **{nations[index].area_km:,.2f}km² ({(nations[index].area_km*(1000^2))/256:,.0f} plots)** compared to **{nations[alt_index].area_km:,.2f}km² ({(nations[alt_index].area_km*(1000^2))/256:,.0f} plots)**. That's around a **{percentage_increase:,.0f}%** increase. **{nations[index].name_formatted}** has roughly **{(nations[index].area_km*(1000^2))/256 / nations[index].total_residents:,.0f}** plots per resident, while **{nations[alt_index].name_formatted}** has **{(nations[alt_index].area_km*(1000^2))/256 / nations[alt_index].total_residents:,.0f}**."

        plottable = {
            f"{nations[index].name_formatted} \nSize total":(nations[index].area_km*(1000^2))/256, 
            f"{nations[index].name_formatted} \nSize per resident":(nations[index].area_km*(1000^2))/256/nations[index].total_residents, 
            f"{nations[alt_index].name_formatted} \nSize total":(nations[alt_index].area_km*(1000^2))/256,
            f"{nations[alt_index].name_formatted} \nSize per resident":(nations[alt_index].area_km*(1000^2))/256/nations[alt_index].total_residents, 
        }
        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Size Comparison: {nation_1.name_formatted} & {nation_2.name_formatted}", 
                    "Nation", 
                    "Size (plots)", 
                    bar
                )
            )
        )

        view = paginator.PaginatorView(embed, content, "newpage", 1, page_image_generators=image_generators, search=False)
        await interaction.followup.send(embed=view.embed, view=view, file=view.attachment)

    @_nations.autocomplete("nation_second")
    async def _second_nation_autocomplete(self, interaction : discord.Interaction, current : str):
        values = interaction.namespace.__dict__

        return [
            app_commands.Choice(name=n.name_formatted, value=n.name_formatted)
            for n in self.client.world.nations if current.lower().replace("_", " ") in n.name_formatted.lower() and values["nation_first"].replace(" ", "_").lower() != n.name_formatted.lower()
        ][:25]
    
    @app_commands.command(name="players", description="Compare two player")
    @app_commands.autocomplete(player_first=autocompletes.player_autocomplete)
    async def _players(self, interaction : discord.Interaction, player_first : str, player_second : str):
        await interaction.response.defer()

        player_1 = self.client.world.get_player(player_first, case_sensitive=False)
        player_2 = self.client.world.get_player(player_second, case_sensitive=False)
        players = [player_1, player_2]

        if not player_1 or not player_2:
            raise e.MildError("One of those players were not found")
        
        if player_1 == player_2:
            raise e.MildError("Cannot use same player twice")

        image_generators = [(graphs.plot_world, (self.client.world, True, players, 20, False))]
        
        embed = discord.Embed(title=f"Player Comparison - {player_1.name} & {player_2.name}", color=s.embed)
        content = f"__Introduction__\n\nThis is a comparison between players **{player_1.name}** and **{player_2.name}**. Click through with the arrows below to see my comparison"

        # Page 2 - Activity
        content += "newpage"

        if player_1.total_online > player_2.total_online:
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        percentage_increase = ((players[index].total_online / players[alt_index].total_online) * 100) - 100

        percentages_in_main_town = [
            ((player_1.visited[list(player_1.visited)[0]]["total"] if len(list(player_1.visited)) > 0 else 0) / player_1.total_online) * 100,
            ((player_2.visited[list(player_2.visited)[0]]["total"] if len(list(player_2.visited)) > 0 else 0) / player_2.total_online) * 100
        ]
        plottable = {
            f"{player_1.name} \nTotal time":player_1.total_online/60, 
            f"{player_1.name} \nTime in {list(player_1.visited)[0]}":player_1.visited[list(player_1.visited)[0]]["total"]/60, 
            f"{player_2.name} \nTotal time":player_2.total_online/60,
            f"{player_2.name} \nTime in {list(player_2.visited)[0]}":player_2.visited[list(player_2.visited)[0]]["total"]/60, 
        }
        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Activity Comparison: {player_1.name} & {player_2.name}", 
                    "Player", 
                    "Activity (minutes)", 
                    bar
                )
            )
        )

        content += f"__Activity__\n\nDuring the {int(self.client.world.total_tracked/3600/24)} days of server tracking, **{players[index].name}** has been online for **{percentage_increase:,.0f}%** longer than **{players[alt_index].name}**, with a total `{functions.generate_time(players[index].total_online)}` compared to `{functions.generate_time(players[alt_index].total_online)}`. {players[index].name} spent **{percentages_in_main_town[index]:,.0f}%** of their time in {list(players[index].visited)[0]}, while {players[alt_index].name} spent **{percentages_in_main_town[alt_index]:,.0f}%** of their time in {list(players[alt_index].visited)[0]}. I last saw **{players[index].name}** online <t:{round(players[index].last_online.timestamp())}:R>, and **{players[alt_index].name}** <t:{round(players[alt_index].last_online.timestamp())}:R>"

        # Page 3 - Town
        content += "newpage"

        if len(player_1.visited) > len(player_2.visited):
            index = 0
            alt_index = 1
        else:
            index = 1
            alt_index = 0
        
        content += f"__Town__\n\n**{players[index].name}** spent **{100-percentages_in_main_town[index]:,.0f}%** of their time outside of **{list(players[index].visited)[0]}**, visiting **{len(players[index].visited)-1}** other towns, while **{players[alt_index].name}** spent **{100-percentages_in_main_town[alt_index]:,.0f}%** of their time outside **{list(players[alt_index].visited)[0]}**, visiting **{len(players[alt_index].visited)-1}** other towns. **{player_1.name}** is {'' if player_1.is_mayor else 'not '}a mayor and **{player_2.name}** is {'also ' if player_2.is_mayor == player_1.is_mayor else ''}{'' if player_2.is_mayor else 'not '}a mayor"

        plottable = {
            f"{player_1.name} \nTotal towns":len(player_1.visited), 
            f"{player_2.name} \nTotal towns":len(player_2.visited),
        }
        image_generators.append( 
            (
                graphs.save_graph, 
                (
                    plottable, 
                    f"Visited Towns comparison: {player_1.name} & {player_2.name}", 
                    "Player", 
                    "No. of towns", 
                    bar
                )
            )
        )

        view = paginator.PaginatorView(embed, content, "newpage", 1, page_image_generators=image_generators, search=False)
        await interaction.followup.send(embed=view.embed, view=view, file=view.attachment)
    
    @_players.autocomplete("player_second")
    async def _second_player_autocomplete(self, interaction : discord.Interaction, current : str):
        values = interaction.namespace.__dict__

        return [
            app_commands.Choice(name=p.name, value=p.name)
            for p in self.client.world.players if current.lower().replace("_", " ") in p.name.lower() and values["player_first"].replace(" ", "_").lower() != p.name.lower()
        ][:25]
    

async def setup(bot : commands.Bot):
    await bot.add_cog(Compare(bot, bot.client))



