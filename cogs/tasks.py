

import pickle 
import discord 
from discord.ext import commands, tasks 
from dynmap import client
import datetime

import asyncio
import typing
import json

import setup as s
from dynmap import world as dynmap_w

nearby_players = {}
prev_players = []

def get_world_task_no_processing(bot : commands.Bot, client : client.Client):

    @tasks.loop(seconds=20)
    async def get_world():

        await client.get_world("RulerEarth")
    
    return get_world

territory_enter_sent = {}

async def notifications(bot : typing.Union[commands.Bot, discord.Client], client : client.Client):
    with open("rulercraft/config.json") as f:
        config = json.load(f)
    
    world = client.cached_worlds["RulerEarth"]

    if "notifications" in config:
        for channel_id_str, channel_settings in config["notifications"].items():
            channel = bot.get_channel(int(channel_id_str))
            nation = world.get_nation(channel_settings["nation"])

            if nation and channel:
                players_in_nation : typing.List[str] = []

                if "territory_enter" in channel_settings:
                    for town in nation.towns:
                        
                        for player in town.near_players:
                            players_in_nation.append(player.name)

                            if channel_id_str not in territory_enter_sent or player.name not in territory_enter_sent[channel_id_str]:

                                tracking_player = client.get_tracking().get_player(player.name)
                                likely_residency_nation = None
                                if tracking_player:
                                    _lr = tracking_player.get_likely_residency()

                                    likely_residency = _lr.town.name_formatted
                                    likely_residency_nation = _lr.town.nation.name_formatted
                                else:
                                    likely_residency = "Unknown"

                                if "ignore_if_resident" in channel_settings and likely_residency_nation == town.nation.name_formatted:
                                    continue

                                if channel_id_str not in territory_enter_sent:
                                    territory_enter_sent[channel_id_str] = {}
                                
                                territory_enter_sent[channel_id_str][player.name] = True

                                embed = discord.Embed(title="Player entered territory", color=s.embed)
                                embed.add_field(name="Player name", value=player.name)
                                embed.add_field(name="Coordinates", value=f"[{player.x:,d}, {player.y:,d}, {player.z:,d}]({client.url}?x={player.x}&z={player.z}&zoom=10)")
                                embed.add_field(name="Town", value=player.current_town.name_formatted)
                                embed.add_field(name="Likely residency", value=f"{likely_residency} ({likely_residency_nation if likely_residency_nation else 'Unknown'})" if likely_residency and likely_residency else "Unknown")
                                embed.set_thumbnail(url=player.avatar)

                                await channel.send(embed=embed)
                

                if channel_id_str in territory_enter_sent:
                    players_to_remove = []

                    for player_name in territory_enter_sent[channel_id_str]:
                        if player_name not in players_in_nation:
                            players_to_remove.append(player_name)
                    
                    for player in players_to_remove:
                        del territory_enter_sent[channel_id_str][player]

def get_world_task(bot : commands.Bot, client_a : client.Client):

    async def task(bot : commands.Bot, client : client.Client):
        global prev_players
        global nearby_players
        with open("rulercraft/server_data.pickle", "rb") as f:
            try:
                server = pickle.load(f)
            except EOFError:
                server = {}
        
        print("1: " + str(datetime.datetime.now()))

        if "total_tracked" not in server:
            server["total_tracked"] = 90000
        
        server["total_tracked"] += 20
        server["last"] = datetime.datetime.now().timestamp()
        
        world : dynmap_w.World = await client.get_world("RulerEarth")
        

        # Get total residents and check territory
        in_territory_this_iteration = []
            
        for town in world.towns:
            
            if not town.bank:
                continue
            if "towns" not in server:
                server["towns"] = {}
            if town.name not in server["towns"]:
                server["towns"][town.name] = {}
            if "visited" not in server["towns"][town.name]:
                server["towns"][town.name]["visited"] = {}
            
            server["towns"][town.name]["total_residents"] = town.total_residents

            if "bank_history" not in server["towns"][town.name]:
                server["towns"][town.name]["bank_history"] = {}
            if "total_residents_history" not in server["towns"][town.name]:
                server["towns"][town.name]["total_residents_history"] = {}
            td = datetime.date.today()
            server["towns"][town.name]["bank_history"][f"{td.year}, {td.month}, {td.day}"] = town.bank
            server["towns"][town.name]["total_residents_history"][f"{td.year}, {td.month}, {td.day}"] = town.total_residents

            for player in town.near_players:
                
                if player.name not in server["towns"][town.name]["visited"]:
                    server["towns"][town.name]["visited"][player.name] = {"total":0, "last":0}
                server["towns"][town.name]["visited"][player.name]["total"] += 20
                server["towns"][town.name]["visited"][player.name]["last"] = datetime.datetime.now().timestamp()

        for player in world.players:
            for town_name in nearby_players:
                if player.name not in in_territory_this_iteration and player.name in nearby_players[town_name]:
                    del nearby_players[town_name][player.name]

        if len(prev_players) > 0:
            for player in world.players:

                # Check user joins and leaves
                nearby_town = player.current_town
                nearby_town = nearby_town.name if nearby_town else "Unknown"

                if "players" not in server:
                    server["players"] = {}
                if player.name not in server["players"]:
                    server["players"][player.name] = {}
                if "activity" not in server["players"][player.name]:
                    server["players"][player.name]["activity"] = {"total":0, "last":0}
                server["players"][player.name]["activity"]["total"] += 20
                server["players"][player.name]["activity"]["last"] = datetime.datetime.now().timestamp()

                server["players"][player.name]["coordinates"] = {"x":player.x, "y":player.y, "z":player.z, "town":nearby_town}
        
        # Remove inactive players and towns and old history data
        remove_players = []
        for name, pl in server["players"].items():
            last = datetime.datetime.fromtimestamp(pl["activity"]["last"])
            if datetime.datetime.now() - last > datetime.timedelta(days=45):
                remove_players.append(name)
        for player_name in remove_players:
            del server["players"][player_name]
        
        #remove_towns = []
        #towns = [t.name for t in world.towns]
        #for town_name in server["towns"].keys():
        #    if town_name not in towns:
        #        remove_towns.append(town_name)
        #for town_name in remove_towns:
        #    del server["towns"][town_name]

        for name, town in server["towns"].items():
            if len(town["bank_history"]) > 45: 
                del town["bank_history"][list(town["bank_history"])[0]]
                del town["total_residents_history"][list(town["total_residents_history"])[0]]


        prev_players = world.players

        with open("rulercraft/server_data.pickle", "wb") as f:
            pickle.dump(server, f)
        
        td = datetime.date.today()
        
        with open(f"rulercraft/server_data_backup_{td.day}_{td.month}_{td.year}.pickle", "wb") as f:
            pickle.dump(server, f)
        
        print("2: " + str(datetime.datetime.now()))
        try:
        
            try:
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(world.players)} online players | /info help"))
            except:
                pass
            
            await notifications(bot, client)
        except Exception as e:
            print(e)

        print("3: " + str(datetime.datetime.now()))
        
        
    

    @tasks.loop(seconds=20)
    async def get_world():
        asyncio.run(task(bot, client_a))

        return "h"
    
    
        
        
    
    return get_world
