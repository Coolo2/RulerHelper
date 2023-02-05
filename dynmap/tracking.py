from __future__ import annotations
import typing 

if typing.TYPE_CHECKING:
    from dynmap.client import Client
    from dynmap import tracking
    from dynmap import world as dynmap_w

import pickle 

import discord
import datetime

class TrackTown():

    def __init__(self, tracking : tracking.Tracking, name : str, data : dict):
        self.tracking = tracking

        self.raw : dict = data 
        self.world : dynmap_w.World = tracking.client.cached_worlds['RulerEarth']
        self.town : dynmap_w.Town = self.world.get_town(name)

        self.bank_history : typing.Dict[str, float] = data["bank_history"]
        self.total_residents_history = data["total_residents_history"] if "total_residents_history" in data else {}
        self.visited = {}

        for p, v in data["visited"].items():
            if p:
                self.visited[p] = v
        
        self.visited = dict(sorted(self.visited.items(), key=lambda x: x[1]["last"], reverse=True))
    
    def __eq__(self, other):
        if not self.town and not other:
            return True
        if other and self.town and other.name == self.town.name:
            return True 
        return False

    
    @property
    def total_activity(self) -> int:

        total = 0 

        for v in self.visited.values():
            total += v["total"]
        
        return total
    
    @property
    def last_activity_timestamp(self) -> int:

        greatest = 0 

        for v in self.visited.values():
            if v["last"] > greatest:
                greatest = round(v["last"])
        
        return greatest
    
    

class TrackPlayer():
    def __init__(self, tracking : tracking.Tracking, name : str, data : dict):
        self.tracking = tracking 
        self.name = name 
        self.raw = data 

        self.last_x = round(data["coordinates"]["x"])
        self.last_y = round(data["coordinates"]["y"])
        self.last_z = round(data["coordinates"]["z"])
        self.last_town = data["coordinates"]["town"]

        self.total_online_seconds = data["activity"]["total"]
        self.last_seen_timestamp = data["activity"]["last"]

        self.likely_residency_set : str = data["likely_residency"] if "likely_residency" in data else None
        self.discord_id_set : int = data["discord_id"] if "discord_id" in data else None
    
    def get_likely_residency(self) -> TrackTown:
        visited : typing.List[str] = self.visited.keys()

        for town_name in visited:
            town = self.tracking.get_town(town_name)

            if town.town and town.town.ruler == self.name:
                return town 
        
        return self.tracking.get_town(self.likely_residency_set) or (self.tracking.get_town(visited[0]) if len(visited) > 0 else None)

    @property 
    def town(self) -> tracking.TrackTown:
        return self.tracking.get_town(self.last_town)

    @property
    def visited(self) -> typing.Dict[str, int]:
        
        visited_towns = {}

        for town in self.tracking.towns:
            if self.name in town.visited:
                if town.town:
                    visited_towns[town.town.name] = town.visited[self.name]
        
        visited_towns = dict(sorted(visited_towns.items(), key=lambda x: x[1]["total"], reverse=True))
        
        return visited_towns
    
    @property 
    def is_mayor(self) -> bool:
        for town in self.tracking.towns:
            if town.town:
                if town.town.ruler == self.name:
                    return True 
        return False
    
    def find_discord(self):

        for guild in self.tracking.client.bot.guilds:
            guild : discord.Guild = guild

            for member in guild.members:
                if str(self.name).lower().replace(".", "") in str(member.nick).lower() or str(self.name).lower().replace(".", "") in str(member.name).lower():
                    return member.id 
        
        return self.discord_id_set
    

class Tracking():
    def __init__(self, client : Client):

        self.client = client 

        with open("rulercraft/server_data.pickle", "rb") as f:
            try:
                self.raw : typing.Dict[str, dict] = pickle.load(f)
            except EOFError:
                self.raw = {}
        
        self.towns : typing.List[TrackTown] = []
        self.players : typing.List[TrackPlayer] = []

        self.total_tracked_seconds = self.raw["total_tracked"]

        for town_name, town in self.raw["towns"].items():
            self.towns.append(TrackTown(self, town_name, town))
        
        for player_name, player in self.raw["players"].items():
            self.players.append(TrackPlayer(self, player_name, player))
        
        self.last : datetime.datetime = datetime.datetime.fromtimestamp(self.raw["last"])
    
    def get_town(self, town_name : str, case_sensitive = True) -> TrackTown:
        
        for town in self.towns:
            if town.town and (town.town.name == town_name or (not case_sensitive and town.town.name.lower() == town_name.lower())):
                return town 
        return None
    
    def get_player(self, player_name : str, case_sensitive = True) -> TrackPlayer:
        
        for player in self.players:
            if player.name == player_name or (not case_sensitive and player.name.lower() == player_name.lower()):
                return player 
        return None
        
