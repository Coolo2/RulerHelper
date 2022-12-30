

import pickle 
import discord 
from discord.ext import commands, tasks 
from dynmap import client
import datetime

import asyncio

from dynmap import world as dynmap_w

nearby_players = {}
prev_players = []

def get_world_task_no_processing(bot : commands.Bot, client : client.Client):

    @tasks.loop(seconds=20)
    async def get_world():

        world = await client.get_world("RulerEarth")
    
    return get_world

def get_world_task(bot : commands.Bot, client_a : client.Client):

    async def task(bot : commands.Bot, client : client.Client):
        global prev_players
        global nearby_players

        with open("rulercraft/server_data.pickle", "rb") as f:
            try:
                server = pickle.load(f)
            except EOFError:
                server = {}

        if "total_tracked" not in server:
            server["total_tracked"] = 90000
        
        server["total_tracked"] += 20
        
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

            for player in town.get_near_players():
                
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
                nearby_town = player.get_current_town()
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


        prev_players = world.players

        with open("rulercraft/server_data.pickle", "wb") as f:
            pickle.dump(server, f)
        
        td = datetime.date.today()
        
        with open(f"rulercraft/server_data_backup_{td.day}_{td.month}_{td.year}.pickle", "wb") as f:
            pickle.dump(server, f)
        
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(world.players)} online players | /info help"))
        
    

    @tasks.loop(seconds=20)
    async def get_world():
        asyncio.run(task(bot, client_a))

        return "h"
    
    
        
        
    
    return get_world
