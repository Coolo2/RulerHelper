
import pickle 
import discord 
from discord.ext import commands, tasks 
import datetime

import aiofiles
import typing
import json
import asyncio

import setup as s
import dynmap
import pprint

counter = 0
territory_enter_sent = {}


async def notifications(bot : typing.Union[commands.Bot, discord.Client], client : dynmap.Client):
    try:
        with open("rulercraft/config.json") as f: config = json.load(f)   
    except IOError:
        config = {}
    

    if "notifications" in config:
        for channel_id_str, channel_settings in config["notifications"].items():
            channel = bot.get_channel(int(channel_id_str))
            nation = client.world.get_nation(channel_settings["nation"])

            if nation and channel:
                players_in_nation : typing.List[str] = []

                if "territory_enter" in channel_settings:
                    for town in nation.towns:
                        
                        for player in town.near_players:
                            players_in_nation.append(player.name)

                            if channel_id_str not in territory_enter_sent or player.name not in territory_enter_sent[channel_id_str]:

                                player = client.world.get_player(player.name)
                                likely_residency_nation = None
                                if player:
                                    _lr = player.likely_residency

                                    if _lr:
                                        likely_residency = _lr.name_formatted
                                        likely_residency_nation = _lr.nation.name_formatted if _lr.nation else ""
                                    else:
                                        likely_residency = "Unknown"
                                else:
                                    likely_residency = "Unknown"

                                if "ignore_if_resident" in channel_settings and town.nation and likely_residency_nation == town.nation.name_formatted:
                                    continue

                                if channel_id_str not in territory_enter_sent:
                                    territory_enter_sent[channel_id_str] = {}
                                
                                territory_enter_sent[channel_id_str][player.name] = True

                                embed = discord.Embed(title="Player entered territory", color=s.embed)
                                embed.add_field(name="Player name", value=player.name)
                                embed.add_field(name="Coordinates", value=f"[{player.x:,d}, {player.y:,d}, {player.z:,d}]({client.url}?x={player.x}&z={player.z}&zoom=10)")
                                embed.add_field(name="Town", value=player.current_town.name_formatted)
                                embed.add_field(name="Likely residency", value=f"{likely_residency} ({likely_residency_nation if likely_residency_nation else 'Unknown'})" if likely_residency and likely_residency else "Unknown")
                                embed.set_thumbnail(url=client.url + player.avatar_path)

                                await channel.send(embed=embed)
                

                if channel_id_str in territory_enter_sent:
                    players_to_remove = []

                    for player_name in territory_enter_sent[channel_id_str]:
                        if player_name not in players_in_nation:
                            players_to_remove.append(player_name)
                    
                    for player in players_to_remove:
                        del territory_enter_sent[channel_id_str][player]

async def refresh_file(client : dynmap.Client) -> dynmap.world.World:
    global counter 

    now = datetime.datetime.now()

    if s.DEBUG_MODE: print("Getting")
    data = await client.http.request("GET", path="/up/world/RulerEarth/0")
    map_data = await client.http.request("GET", path="/tiles/_markers_/marker_RulerEarth.json")
    if s.DEBUG_MODE: print("Got")

    world = await load_file()
    if not world: print("Couldn't load world.");return 
    
    if s.DEBUG_MODE: print("1: " + str(datetime.datetime.now()))

    if s.MIGRATE_OLD_SAVEFILE:
        async with aiofiles.open("rulercraft/old_data.pickle", "rb") as f:
            old_data = pickle.loads(await f.read())

    world.total_tracked += s.REFRESH_INTERVAL

    world.is_stormy = data["hasStorm"]
    world.is_thundering = data["isThundering"]
    world.time = (datetime.datetime.combine(datetime.date(1,1,1),datetime.time(0, 0, 0)) + datetime.timedelta(hours=6) + datetime.timedelta(hours=data["servertime"]/1000)).time()
    
    online_players : typing.Dict[str, dict] = {}
    for raw_player in data["players"]:
        online_players[raw_player["account"]] = raw_player

        if raw_player["account"] not in world.players:
            p = dynmap.world.Player(world)
            p.load_data(raw_player)

            world.players.append(p)
        
    
    # Create offline players if no longer online
    for player in world.players.copy():
        if player.name in online_players:
            player.online = True
            player.load_data(online_players[player.name])
        else:
            player.online = False
    
    for town in world.towns:
        town.points = []
        
    

    for area_name, area_data in map_data["sets"]["towny.markerset"]["areas"].items():
        
        if area_data["label"] not in world.towns:
            town = dynmap.world.Town(world, area_data=area_data)

            world.towns.append(town)
        else:
            town = world.get_town(area_data["label"])

        town.add_area_data(area_data)
        town.last_updated = datetime.datetime.now()
    
    for marker_name, marker_data in map_data["sets"]["towny.markerset"]["markers"].items():
        for town in world.towns:
            if town.name == marker_data["label"]:
                town.x = round(marker_data["x"])
                town.y = round(marker_data["y"])
                town.z = round(marker_data["z"])
                town.icon = marker_data["icon"]
        
    for town in world.towns:
        if town.culture and town.culture not in world.cultures:
            world.cultures.append(town.culture)
        if town.religion and town.religion not in world.religions:
            world.religions.append(town.religion)
        if town.nation and town.nation not in world.nations:
            world.nations.append(town.nation)

        td = datetime.date.today()
        town.bank_history[f"{td.year}, {td.month}, {td.day}"] = town.bank
        town.total_residents_history[f"{td.year}, {td.month}, {td.day}"] = town.total_residents
        
        for player in town.near_players:
            if player.name not in town.visited:
                town.visited[player.name] = {"total":0, "last":0}
            town.visited[player.name]["total"] += s.REFRESH_INTERVAL
            town.visited[player.name]["last"] = datetime.datetime.now()
        
        # Prune
        for player_name, value in town.visited.copy().items():
            if datetime.datetime.now() - value["last"] > datetime.timedelta(days=45):
                del town.visited[player_name]

        if len(town.bank_history) > 45: 
            del town.bank_history[list(town.bank_history)[0]]
            del town.total_residents_history[list(town.total_residents_history)[0]]

    # Prune
    for player in world.players.copy():
        
        if player.online:
            player.total_online += s.REFRESH_INTERVAL
            player.last_online = datetime.datetime.now()
        
        if player.last_online and datetime.datetime.now() - player.last_online > datetime.timedelta(days=45):
            world.players.remove(player)
    
    for town in world.towns.copy():
        if now - town.last_updated > datetime.timedelta(hours=1, minutes=30):
            world.towns.remove(town)

            #await bot.get_channel(985596858992853122).send(f"removed town {town_name}")
    
    if s.MIGRATE_OLD_SAVEFILE:
        for player in world.players:
            if not player.loaded_old_data and player.name in old_data["players"]:
                player.total_online = old_data["players"][player.name]["activity"]["total"]
                player.last_online = datetime.datetime.fromtimestamp(old_data["players"][player.name]["activity"]["last"])
                player.loaded_old_data = True
        
        for town in world.towns:
            if not town.loaded_old_data and town.name in old_data["towns"]:
                for player_name, visited_data in old_data["towns"][town.name]["visited"].items():
                    town.visited[player_name] = {"total":visited_data["total"], "last":datetime.datetime.fromtimestamp(visited_data["last"])}
                town.bank_history = old_data["towns"][town.name]["bank_history"]
                town.total_residents_history = old_data["towns"][town.name]["total_residents_history"]
                town.loaded_old_data = True
        
        if not world.loaded_old_data:
            world.total_tracked = old_data["total_tracked"]
            world.loaded_old_data = True
    
    world.process_time = datetime.datetime.now() - now
    world.last_refreshed = datetime.datetime.now()
    
    async with aiofiles.open('rulercraft/server_data.pickle', 'wb') as f:
        #await f.write(pickle.dumps(world))
        await f.write(pickle.dumps(world.to_dict()))
    
    if s.BACKUP_SAVEFILE:
        td = datetime.date.today()
        async with aiofiles.open(f"rulercraft/server_data_backup_{td.day}_{td.month}_{td.year}.pickle", 'wb') as f:
            await f.write(pickle.dumps(world))
    
    if s.DEBUG_MODE: print("2: " + str(datetime.datetime.now()))
    
    counter += 1
    

    return world

async def load_file(recursion=0) -> dynmap.world.World:
    world = dynmap.world.World()

    try:
        async with aiofiles.open('rulercraft/server_data.pickle', 'rb') as f:
            #load = pickle.loads(await f.read())
            load = pickle.loads(await f.read())

            if type(load) != dict and recursion <= 3:
                await asyncio.sleep(2)
                if s.DEBUG_MODE: print("Loading file failed. Trying again")
                return await load_file(recursion=recursion+1)
            
            if type(load) == dict:
                world.load_old_world(load)
    except FileNotFoundError:
        pass
    except EOFError:
        if recursion <= 3:
            await asyncio.sleep(2)
            if s.DEBUG_MODE: print("Loading file failed. Trying again")
            return await load_file(recursion=recursion+1)
    except pickle.UnpicklingError as e:
        print(e)
        if recursion <= 3:
            await asyncio.sleep(2)
            if s.DEBUG_MODE: print("Loading file failed. Trying again")
            return await load_file(recursion=recursion+1)
    
    return world

async def refresh_status(bot : commands.Bot, client_a : dynmap.Client):
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=((s.STATUS_EXTRA + " | ") if s.STATUS_EXTRA != "" else "") + f"{len(client_a.world.online_players)} online players | /info help"))
    except:
        pass

def notifications_task(bot : commands.Bot, client_a : dynmap.Client):
    @tasks.loop(seconds=s.REFRESH_INTERVAL)
    async def get_world():
        if client_a.world:
            await notifications(bot, client_a)
            await refresh_status(bot, client_a)
    
    return get_world

def load_and_update_file_task(bot : commands.Bot, client_a : dynmap.Client):
    @tasks.loop(seconds=s.REFRESH_INTERVAL)
    async def get_world():
        
        refresh = await refresh_file(client_a)
        client_a.world = refresh
        
        
        await notifications(bot, client_a)
        await refresh_status(bot, client_a)
    
    return get_world
