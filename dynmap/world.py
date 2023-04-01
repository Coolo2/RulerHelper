from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from dynmap.client import Client
    from dynmap import world as dynmap_w

import typing
import datetime

from bs4 import BeautifulSoup
import math

import numpy as np
import shapely.geometry
from funcs import functions

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
    
    @property
    def current_town(self) -> dynmap_w.Town:

        world : dynmap_w.World = self.client.cached_worlds["RulerEarth"]

        nearby_town = None

        for town in world.towns:
            if town.is_coordinate_in_town(self.x, self.z):
                nearby_town = town

        return nearby_town
    
    def __eq__(self, other):
        if other and other.name == self.name:
            return True 
        return False
    
    def to_dict(self):
        return {
            "name":self.name, "health":self.health, "armor":self.armor, "coordinates":[self.x, self.y, self.z], "avatar":self.avatar
        }



class _CultureOrReligion:
    # Progressive generation
    def __init__(self, CRType : str, world : dynmap_w.World, name : str):
        self.name = name 
        self.world = world 
        self.type = CRType
    
    @property 
    def towns(self) -> typing.List[dynmap_w.Town]:
        _towns = []
        for town in self.world.towns:
            if town.culture == self or town.religion == self:
                _towns.append(town)
        return _towns
    
    @property 
    def total_residents(self) -> int:
        c = 0
        for town in self.towns:
            c += town.total_residents 
        return c
    
    def __eq__(self, other):
        if other and other.name == self.name:
            return True 
        return False

class Culture(_CultureOrReligion):
    def __init__(self, world : dynmap_w.World, name : str):
        super().__init__("culture", world, name)

class Religion(_CultureOrReligion):
    def __init__(self, world : dynmap_w.World, name : str):
        super().__init__("religion", world, name)
    @property 
    def total_followers(self):
        return self.total_residents


class Nation:
    def __init__(self, world : dynmap_w.World, name : str):
        self.name = name 

        self.world = world
    
    @property 
    def capital(self) -> dynmap_w.Town:
        for town in self.towns:
            if town.icon == "king":
                return town 
        return None
    
    @property 
    def name_formatted(self):
        return self.name.replace("_", " ").title()
    
    @property 
    def area_km(self):
        
        total_area = 0

        for town in self.towns:
            total_area += town.area_km

        return total_area
    
    @property 
    def towns(self) -> typing.List[dynmap_w.Town]:
        towns = []

        for town in self.world.towns:
            if town.nation and town.nation.name == self.name:
                towns.append(town)
        
        return towns
    
    @property 
    def total_residents(self):
        total_residents = 0
        for town in self.towns:
            if town.total_residents:
                total_residents += town.total_residents
            
        return total_residents
    
    @property 
    def total_bank(self) -> float:
        total_bank = 0
        for town in self.towns:
            if town.total_residents:
                total_bank += town.bank
            
        return total_bank
    
    @property 
    def religion_make_up(self) -> typing.Dict[str, int]:
        d = {}
        for town in self.towns:
            if town.religion:
                if town.religion.name not in d:
                    d[town.religion.name] = 0
                d[town.religion.name] += town.total_residents
        d = dict(sorted(d.items(), key=lambda x: x[1], reverse=True))
        return d
    
    @property 
    def culture_make_up(self) -> typing.Dict[str, int]:
        d = {}
        for town in self.towns:
            if town.culture:
                if town.culture.name not in d:
                    d[town.culture.name] = 0
                d[town.culture.name] += town.total_residents
        d = dict(sorted(d.items(), key=lambda x: x[1], reverse=True))
        return d
    
    @property 
    def borders(self) -> typing.List[dynmap_w.Nation]:
        borders = []
        for t in self.towns:
            for town in t.borders:
                if town.nation and town.nation not in borders and town.nation != self:
                    borders.append(town.nation)
        
        return borders

    def __eq__(self, other):
        if other and other.name == self.name:
            return True 
        return False
    
    def to_dict(self):
        return {"name":self.name, "total_residents":self.total_residents, "towns":[t.name for t in self.towns], "plots":round((self.area_km*(1000^2))/256), "capital":self.capital.name}

    def get_notable_statistics(self, top_under_percentage : int = 10) -> typing.List[str]:
        stats = []
        
        stats.append(f"{self.name_formatted}'s average town bank balance is ${self.total_bank/len(self.towns):,.2f}")

        rank_stats : typing.List[typing.List[int, str]] = []

        nations_residents = list(sorted(self.world.nations, key=lambda x:x.total_residents, reverse=True))
        if (nations_residents.index(self) / len(nations_residents)) * 100 < top_under_percentage:
            rank_stats.append([nations_residents.index(self), f"{self.name_formatted} is the {functions.ordinal(nations_residents.index(self)+1)} most populous nation"])
        
        nations_area = list(sorted(self.world.nations, key=lambda x:x.area_km, reverse=True))
        if (nations_area.index(self) / len(nations_area)) * 100 < top_under_percentage:
            rank_stats.append([nations_area.index(self), f"{self.name_formatted} is the {functions.ordinal(nations_area.index(self)+1)} biggest nation (area)"])
        
        nations_towns = list(sorted(self.world.nations, key=lambda x:len(x.towns), reverse=True))
        if (nations_towns.index(self) / len(nations_towns)) * 100 < top_under_percentage:
            rank_stats.append([nations_towns.index(self), f"{self.name_formatted} is {functions.ordinal(nations_towns.index(self)+1)} on the total town leaderboard"])
        
        rank_stats = [i[1] for i in sorted(rank_stats, key=lambda x: x[0])]
        stats += rank_stats

        return stats

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

        self.total_residents : int = None 
        self.nation : Nation = None
        self.daily_tax : float = None
        self.bank : float = None
        self.ruler : str = None
        self.public : bool = None
        self.founded : datetime.date = None
        self.culture : Culture = None
        self.religion : Religion = None

        self._parse_desc()
    
    def towns_within_range(self, blocks : int) -> typing.List[dynmap_w.Town]:
        towns = []
        for town in self.world.towns:
            distance = math.sqrt((town.x - self.x)**2 + (town.z - self.z)**2)
            if distance <= blocks:
                towns.append(town)
        
        return towns

    @property 
    def age(self) -> int:
        return (datetime.date.today() - self.founded).days

    @property 
    def mayor(self) -> dynmap_w.Player:
        return self.world.get_player(self.ruler)
    
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
            
            if tag.string and "Resident Tax:" in tag.string:
                try:
                    self.daily_tax = float(tag.parent.get_text().split("Resident Tax: ")[1].replace("%", ""))
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
                    if tag.get_text().split(" ")[1].replace(" ", "") == "":
                        self.nation = None
                    else:
                        self.nation = Nation(self.world, tag.get_text().split(" ")[1])
                except:
                    pass
                    
            if tag.string and "Public:" in tag.string:
                try:
                    public = tag.parent.get_text().split("Public: ")[1]
                    self.public = True if public == "true" else False
                except:
                    pass

            if tag.string and "Founded:" in tag.string:
                try:
                    self.founded = datetime.datetime.strptime(tag.parent.get_text().split("Founded: ")[1], "%b %d %Y").date()
                except:
                    pass
            
            if tag.string and "🕎 Culture -" in tag.string:
                try:
                    self.culture = Culture(self.world, tag.parent.get_text().split("🕎 Culture - ")[1])
                    if self.culture.name.replace(" ", "") == "":
                        self.culture = None
                except:
                    pass
            
            if tag.string and "Town Religion -" in tag.string:
                try:
                    self.religion = Religion(self.world, tag.parent.get_text().split("Town Religion - ")[1])
                except:
                    pass
    
    def is_coordinate_in_town(self, x : int, z : int) -> bool:

        for point_group in self.points:
        
            poly = shapely.geometry.Polygon(point_group)
            point = shapely.geometry.Point(x, z)

            if poly.contains(point):
                return True
        
        return False

    @property
    def near_players(self) -> typing.List[Player]:

        players : typing.List[Player] = []

        for player in self.world.players:        
            if self.is_coordinate_in_town(player.x, player.z):
                players.append(player)
        

        
        return players

    @property 
    def borders(self) -> typing.List[dynmap_w.Town]:
        borders = []
        for self_point_group in self.points:
            self_polygon = shapely.geometry.Polygon(self_point_group)

            for town in self.world.towns:
                for point_group in town.points:
                    if town not in borders and town != self and town.name not in ["Rulerspawn", "Unclaimed"]:
                        polygon = shapely.geometry.Polygon(point_group)
                        if polygon.intersects(self_polygon):
                            borders.append(town)
        
        return borders

    def __eq__(self, other):
        if other and other.name == self.name:
            return True 
        return False
    
    def to_dict(self):
        return {
            "name":self.name,
            "mayor":self.ruler,
            "bank":self.bank,
            "border_color":self.border_color,
            "fill_color":self.fill_color,
            "total_residents":self.total_residents,
            "taxes":self.daily_tax,
            "nation":self.nation.name if self.nation else None,
            "spawn":[self.x, self.y, self.z],
            "icon":self.icon
        }





class World():
    def __init__(self, client, data : dict, map_data : dict):
        self.client = client

        self._parse_data(data, map_data)

    @property 
    def total_residents(self) -> int:
        total = 0
        for town in self.towns:
            total += town.total_residents
        return total
    
    @property 
    def total_area_km(self) -> float:
        total = 0
        for town in self.towns:
            total += town.area_km
        return total
    
    @property 
    def total_town_bank(self) -> float:
        total = 0
        for town in self.towns:
            total += town.bank
        return total

    def _parse_data(self, data : dict, map_data : dict):

        self.is_stormy = data["hasStorm"]
        self.is_thundering = data["isThundering"]
        self.time = (datetime.datetime.combine(datetime.date(1,1,1),datetime.time(0, 0, 0)) + datetime.timedelta(hours=6) + datetime.timedelta(hours=data["servertime"]/1000)).time()
        
        self.players : typing.List[Player] = []
        self.nations : typing.List[Nation] = []
        self.cultures : typing.List[Culture] = []
        self.religions : typing.List[Religion] = []

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
            if town.culture and town.culture not in self.cultures:
                self.cultures.append(town.culture)
            if town.religion and town.religion not in self.religions:
                self.religions.append(town.religion)
            if town.nation and town.nation not in self.nations:
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
    
    def get_nation(self, name : str, case_sensitive = True) -> dynmap_w.Nation:
        for nation in self.nations:
            if nation.name == name or (not case_sensitive and nation.name.lower() == name.lower()):
                return nation 

        return None   
    
    def get_culture(self, name : str, case_sensitive = True) -> dynmap_w.Nation:
        for culture in self.cultures:
            if culture.name == name or (not case_sensitive and culture.name.lower() == name.lower()):
                return culture 

        return None   
    
    def get_religion(self, name : str, case_sensitive = True) -> dynmap_w.Nation:
        for religion in self.religions:
            if religion.name == name or (not case_sensitive and religion.name.lower() == name.lower()):
                return religion 

        return None   

    def get_all_town_borders(self):

        response : typing.Dict[str, typing.List[Nation]] = {}

        for town in self.towns:
            if town.name not in response:
                borders = town.borders

                response[town.name] = borders
                for borders_town in borders:
                    if borders_town.name not in response:
                        response[borders_town.name] = []
                    response[borders_town.name].append(town)
        return response
    
    def to_dict(self):
        return {
            "players":[p.to_dict() for p in self.players],
            "towns":[t.to_dict() for t in self.towns],
            "nations":[n.to_dict() for n in self.nations]
        }
    
    

