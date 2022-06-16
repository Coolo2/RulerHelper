from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from dynmap.client import Client
    from dynmap import world as dynmap_w

import typing
import datetime

from bs4 import BeautifulSoup
import math

import shapely.geometry

def calculateDistance(coordinate1, coordinate2):
    dist = math.sqrt((coordinate1[1] - coordinate1[0])**2 + (coordinate2[1] - coordinate2[0])**2)
    return dist

class Player:

    def __init__(self, client : Client, data : dict):
        self.world = data["world"] 
        self.armor = data["armor"] 
        self.name = data["account"] 
        self.x = round(data["x"])
        self.y = round(data["y"])
        self.z = round(data["z"])
        self.health = data["health"]

        self.distance = None # To be updated with get_town_nearby

        self.client = client

        self.avatar = f"{client.url}/tiles/faces/32x32/{self.name}.png"
    
    def get_current_town(self) -> dynmap_w.Town:

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]

        nearby_town = None

        for town in world.towns:
            if town.is_coordinate_in_town(self.x, self.z):
                nearby_town = town

        return nearby_town
    

class Nation:
    def __init__(self, world, name : str):
        self.name = name 

        self.world = world
    
    @property 
    def name_formatted(self):
        return self.name.replace("_", " ").title()
    
    @property 
    def area_km(self):
        
        total_area = 0

        for town in self.get_towns():
            total_area += town.area_km

        return total_area
    
    def get_towns(self) -> typing.List[dynmap_w.Town]:
        towns = []

        for town in self.world.towns:
            if town.nation and town.nation.name == self.name:
                towns.append(town)
        
        return towns
    
    def get_total_residents(self):
        total_residents = 0
        for town in self.get_towns():
            if town.total_residents:
                total_residents += town.total_residents
            
        return total_residents

class Town:

    def __init__(self, world : dynmap_w.World, area_data : dict = None):
        self.world = world

        self.name : str = None 
        self.desc : str = None

        self.border_color : str = None 
        self.fill_color : str = None

        self.points = []

        if area_data:
            self.name = area_data["label"]
            self.desc = area_data["desc"]

            self.border_color = area_data["color"]
            self.fill_color = area_data["fillcolor"]

            self.add_area_data(area_data)
        
        # Added externally

        self.x : int = None 
        self.y : int = None 
        self.z : int = None 
        self.icon : str = None 

        self._parse_desc()
    
    @property 
    def name_formatted(self):
        return self.name.replace("_", " ").title()
    
    @property 
    def area_km(self):

        total_area = 0

        for point_group in self.points:
        
            poly = shapely.geometry.Polygon(point_group)
            total_area += poly.area 

        return total_area / (1000^2)

        
    
    def add_area_data(self, area_data):

        new_data = []

        for i in range(len(area_data["x"])):
            new_data.append([area_data["x"][i], area_data["z"][i]])
        
        self.points.append(new_data)

    def describe(self):

        long = None
        lat = None
        phrase = None

        if self.x > 1000:
            long = "east"
        if self.x < -10000:
            long = "west"
        
        if self.z < -7000:
            lat = "north"
        if self.z > 0:
            lat = "south"
        
        if lat and not long:
            phrase = lat.title()
        if long and not lat:
            phrase = long.title()
        if lat and long:
            phrase = f"{lat.title()} {long.title()}"

        if not phrase:
            phrase = "Center"
        
        return phrase
        

    def _parse_desc(self):
        desc = self.desc 

        # Bank, founded

        self.total_residents = None 
        self.nation : Nation  = None
        self.daily_tax = None
        self.bank = None
        self.ruler = None

        if not desc:
            return

        soup = BeautifulSoup(desc, "html.parser")

        tags = soup.find_all("span")

        for tag in tags:
            
            if tag.string and "Residents:" in tag.string:
                try:
                    self.total_residents = int(tag.parent.get_text().split("Residents: ")[1])
                except:
                    pass
            
            if tag.string and "Daily Tax:" in tag.string:
                try:
                    self.daily_tax = float(tag.parent.get_text().split("Daily Tax: ")[1].replace("%", ""))
                except:
                    pass
            
            if tag.string and "Ruler:" in tag.string:
                try:
                    self.ruler = tag.parent.parent.get_text().split("Ruler: ")[1].split(" ")[0]
                except:
                    pass
            
            if tag.string and "Bank:" in tag.string:
                try:
                    self.bank = float(tag.parent.get_text().split("Bank: ")[1].replace(" Dollars", "").replace(",", ""))
                except:
                    pass

            if tag.get_text() and "🎌 " in tag.get_text():
                
                try:
                    self.nation = Nation(self.world, tag.get_text().split(" ")[1])
                except:
                    pass
    
    def is_coordinate_in_town(self, x : int, z : int) -> bool:

        for point_group in self.points:
        
            poly = shapely.geometry.Polygon(point_group)
            point = shapely.geometry.Point(x, z)

            if poly.contains(point):
                return True
        
        return False

    def get_near_players(self) -> typing.List[Player]:

        players : typing.List[Player] = []

        for player in self.world.players:        
            if self.is_coordinate_in_town(player.x, player.z):
                players.append(player)
        

        
        return players







class World():
    def __init__(self, client, data : dict, map_data : dict):
        self.client = client

        self._parse_data(data, map_data)

    def _parse_data(self, data : dict, map_data : dict):

        self.is_stormy = data["hasStorm"]
        self.is_thundering = data["isThundering"]
        self.time = (datetime.datetime.combine(datetime.date(1,1,1),datetime.time(0, 0, 0)) + datetime.timedelta(hours=6) + datetime.timedelta(hours=data["servertime"]/1000)).time()
        
        self.players : typing.List[Player] = []
        self.nations : typing.List[Nation] = []

        for player in data["players"]:
            self.players.append(Player(self.client, player))
        
        self.towns : typing.List[Town] = []

        for area_name, area_data in map_data["sets"]["towny.markerset"]["areas"].items():

            
            if area_data["label"] not in [t.name for t in self.towns]:
                self.towns.append(Town(self, area_data=area_data))
            else:
                t = self.get_town(area_data["label"])
                t.add_area_data(area_data)
        
        for marker_name, marker_data in map_data["sets"]["towny.markerset"]["markers"].items():
            for town in self.towns:
                if town.name == marker_data["label"]:
                    town.x = round(marker_data["x"])
                    town.y = round(marker_data["y"])
                    town.z = round(marker_data["z"])
                    town.icon = marker_data["icon"]

                    #town.points.append([town.x, town.z])
                        
        
        for town in self.towns:
            if town.nation and town.nation.name not in [n.name for n in self.nations if n != None] and town.nation.name.replace(" ", "") != "":

                self.nations.append(town.nation)
                        


    def get_player(self, name : str, case_sensitive = True):
        for player in self.players:
            if player.name == name or (not case_sensitive and player.name.lower() == name.lower()):
                return player 
        
        return None

    def get_town(self, name : str, case_sensitive = True):
        for town in self.towns:
            if town.name == name or (not case_sensitive and town.name.lower() == name.lower()):
                return town 

        return None    
    
    def get_nation(self, name : str, case_sensitive = True):
        for nation in self.nations:
            if nation.name == name or (not case_sensitive and nation.name.lower() == name.lower()):
                return nation 

        return None   
    
    
