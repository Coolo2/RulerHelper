from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from dynmap import world as dynmap_w

import typing
import datetime

import warnings 
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

from bs4 import BeautifulSoup
import math

import shapely.geometry
from funcs import functions

import discord

VERSION = 1
IGNORE_ATTRS = ["world", "raw", "desc"]

def calculateDistance(coordinate1, coordinate2):
    dist = math.sqrt((coordinate1[1] - coordinate1[0])**2 + (coordinate2[1] - coordinate2[0])**2)
    return dist

def to_dict(obj : typing.Callable):
    {k:(v.to_dict() if hasattr(v, "to_dict") else [(i.to_dict() if hasattr(i, "to_dict") else i.__dict__ if hasattr(i, "__dict__") else i) for i in v] if hasattr(v, "__iter__") and type(v) != str else v.__dict__ if hasattr(v, "__dict__") else v)  for k, v in obj.__dict__.items()}

    d = {}
    
    for k, v in obj.__dict__.items():
        if k in IGNORE_ATTRS: continue

        if hasattr(v, "to_dict"):
            d[k] = v.to_dict()
        elif hasattr(v, "__iter__") and type(v) != str:
            d[k] = [] 
            for i in v:
                if hasattr(i, "to_dict"):
                    d[k].append(i.to_dict()) 
                elif hasattr(i, "__dict__"): 
                    o = {}
                    for k2, v2 in i.__dict__.items():
                        if k2 in IGNORE_ATTRS: continue 
                        o[k2] = v2
                    d[k].append(o)  
                else: 
                    d[k].append(i)
        elif hasattr(v, "__dict__"):
            d[k] = {}
            for k2, v2 in v.__dict__.items():
                if k2 in IGNORE_ATTRS: continue 
                d[k][k2] = v2
        else: 
            d[k] = v
    
    return d

class Player:

    def __init__(self, world : dynmap_w.World):
        self.raw : dict = None 

        self.world_name : str = None 
        self.armor : int = None
        self.name : str = None
        self.x : int = None
        self.y : int = None
        self.z : int = None
        self.health : int = None

        self.distance = None # To be updated with get_town_nearby
        self.online : bool = None

        self.total_online : int = 0
        self.last_online : datetime.datetime = None

        self.world = world

        self.avatar_path : str = None

        self.likely_residency_set : str = None 
        self.discord_id_set : int = None

        self.loaded_old_data = False
    
    def load_data(self, data : dict):
        self.raw = data 

        self.world_name = data["world"]
        self.armor = data["armor"] 
        self.name = data["account"] 
        self.x = round(data["x"])
        self.y = round(data["y"])
        self.z = round(data["z"])
        self.health = data["health"]
        self.avatar_path = f"/tiles/faces/32x32/{self.name}.png"

    @property
    def current_town(self) -> dynmap_w.Town:

        nearby_town = None

        for town in self.world.towns_future:
            if town.is_coordinate_in_town(self.x, self.z):
                nearby_town = town

        return nearby_town

    @property 
    def is_mayor(self) -> bool:
        for town in self.world.towns_future:
            if town.ruler == self.name:
                return True 
        return False

    @property
    def visited(self) -> typing.Dict[str, int]:
        
        visited_towns = {}

        for town in self.world.towns_future:
            if self.name in town.visited:
                visited_towns[town.name] = town.visited[self.name]
        
        visited_towns = dict(sorted(visited_towns.items(), key=lambda x: x[1]["total"], reverse=True))
        
        return visited_towns

    @property 
    def likely_residency(self) -> dynmap_w.Town:
        if self.likely_residency_set:
            return self.world.get_town(self.likely_residency_set)
        
        visited : typing.List[str] = self.visited.keys()

        for town_name in visited:
            town = self.world.get_town(town_name)

            if town and town.ruler == self.name:
                return town 
        
        return self.world.get_town(list(visited)[0]) if len(visited) > 0 else None

    def get_notable_statistics(self, top_under_percentage : int = 10) -> typing.List[str]:
        stats = []

        rank_stats : typing.List[typing.List[int, str]] = []

        players_activity = list(sorted(self.world.players, key=lambda x:x.total_online, reverse=True))
        if (players_activity.index(self) / len(players_activity)) * 100 < top_under_percentage:
            rank_stats.append([players_activity.index(self), f"{self.name} is the {functions.ordinal(players_activity.index(self)+1)} most active player"])
        
        players_visited = list(sorted(self.world.players, key=lambda x:len(x.visited), reverse=True))
        if (players_visited.index(self) / len(players_visited)) * 100 < top_under_percentage:
            rank_stats.append([players_visited.index(self), f"{self.name} is {functions.ordinal(players_visited.index(self)+1)} on the visited towns leaderboard"])
        
        rank_stats = [i[1] for i in sorted(rank_stats, key=lambda x: x[0])]
        stats += rank_stats

        return stats

    def find_discord(self, bot : discord.Client):
        
        if self.discord_id_set:
            return self.discord_id_set

        for guild in bot.guilds:
            guild : discord.Guild = guild

            for member in guild.members:
                if str(self.name).lower().replace(".", "") in str(member.nick).lower() or str(self.name).lower().replace(".", "") in str(member.name).lower():
                    return member.id 
    
    @classmethod
    def load_old(self, world : dynmap_w.World, old_player : dict):
        s = self(world)
        #s.load_data(old_player["raw"])

        for attr_name, attr_value in old_player.items():
            if attr_name in IGNORE_ATTRS:
                continue
            setattr(s, attr_name, attr_value)
        
        return s

    def __eq__(self, other):
        if other and other == self.name or (hasattr(other, "name") and other.name == self.name):
            return True 
        return False

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

    @classmethod
    def load_old(self, world : dynmap_w.World, old_cr : dict):
        s = self(world, old_cr["name"])

        for attr_name, attr_value in old_cr.items():
            if attr_name in IGNORE_ATTRS:
                continue
            setattr(s, attr_name, attr_value)
        
        return s
    
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

    @classmethod
    def load_old(self, world : dynmap_w.World, old_nation : dict):
        s = self(world, old_nation["name"])

        for attr_name, attr_value in old_nation.items():
            if attr_name in IGNORE_ATTRS:
                continue
            setattr(s, attr_name, attr_value)
        
        return s

    def __eq__(self, other):
        if other and other == self.name or (hasattr(other, "name") and other.name == self.name):
            return True 
        return False
    
    

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

        self.bank_history : typing.Dict[str, float] = {}
        self.total_residents_history : typing.Dict[str, typing.Union[int, datetime.datetime]] = {}
        self.visited : typing.Dict[str, typing.Dict[str, typing.Union[int, datetime.datetime]]] = {}

        self.last_updated : datetime.datetime = None
        self.loaded_old_data = False

        if area_data:
            self.add_area_data(area_data)
            # Add world data seperately

        
    
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
        old_desc = self.desc

        self.name = area_data["label"]
        

        self.border_color = area_data["color"]
        self.fill_color = area_data["fillcolor"]

        new_data = []

        for i in range(len(area_data["x"])):
            new_data.append([area_data["x"][i], area_data["z"][i]])
        
        self.points.append(new_data)
        if old_desc != area_data["desc"]:
            self.desc = area_data["desc"]
            self._parse_desc()

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
        
        soup = BeautifulSoup(desc, "html.parser", from_encoding="utf8")

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

        for player in self.world.online_players:        
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
    
    @property
    def total_activity(self) -> int:

        total = 0 

        for v in self.visited.values():
            total += v["total"]
        
        return total

    @property
    def last_activity(self) -> datetime.datetime:

        greatest = datetime.datetime(year=2020, month=1, day=2)

        for v in self.visited.values():
            if v["last"] > greatest:
                greatest = v["last"]
        
        return greatest

    def get_notable_statistics(self, top_under_percentage : int = 10) -> typing.List[str]:
        stats = []

        if len(self.points) > 1:
            detatched_area_km = 0
            for point_group in self.points:
                poly = shapely.geometry.Polygon(point_group)
                if not poly.contains(shapely.geometry.Point(self.x, self.z)):
                    detatched_area_km += poly.area / (1000^2)
            detatched_area_percentage = (detatched_area_km / self.area_km) * 100

            stats.append(f"Detatched territories make up {detatched_area_percentage:,.0f}% of {self.name_formatted}'s claims")

        rank_stats : typing.List[typing.List[int, str]] = []

        towns_residents = list(sorted(self.world.towns, key=lambda x:x.total_residents, reverse=True))
        if (towns_residents.index(self) / len(towns_residents)) * 100 < top_under_percentage:
            rank_stats.append([towns_residents.index(self), f"{self.name_formatted} is the {functions.ordinal(towns_residents.index(self)+1)} most populous town"])
        
        towns_balance = list(sorted(self.world.towns, key=lambda x:x.bank, reverse=True))
        if (towns_balance.index(self) / len(towns_balance)) * 100 < top_under_percentage:
            rank_stats.append([towns_balance.index(self), f"{self.name_formatted} is the {functions.ordinal(towns_balance.index(self)+1)} richest town"])
        
        towns_activity = list(sorted(self.world.towns, key=lambda x:x.total_activity, reverse=True))
        if (towns_activity.index(self) / len(towns_activity)) * 100 < top_under_percentage:
            rank_stats.append([towns_activity.index(self), f"{self.name_formatted} is the {functions.ordinal(towns_activity.index(self)+1)} most active town"])
        
        towns_area = list(sorted(self.world.towns, key=lambda x:x.area_km, reverse=True))
        if (towns_area.index(self) / len(towns_area)) * 100 < top_under_percentage:
            rank_stats.append([towns_area.index(self), f"{self.name_formatted} is the {functions.ordinal(towns_area.index(self)+1)} biggest town"])

        towns_age = list(sorted(self.world.towns, key=lambda x:x.age, reverse=True))
        if (towns_age.index(self) / len(towns_age)) * 100 < top_under_percentage:
            rank_stats.append([towns_age.index(self), f"{self.name_formatted} is the {functions.ordinal(towns_age.index(self)+1)} oldest town"])
        
        rank_stats = [i[1] for i in sorted(rank_stats, key=lambda x: x[0])]
        stats += rank_stats

        return stats

    @classmethod
    def load_old(self, world : dynmap_w.World, old_town : dict):
        s = self(world, None)

        for attr_name, attr_value in old_town.items():
            if attr_name in IGNORE_ATTRS:
                continue
            setattr(s, attr_name, attr_value)
        
        return s

    def __eq__(self, other):
        if other and other == self.name or (hasattr(other, "name") and other.name == self.name):
            return True 
        return False
    
    



class VisitedPlayer(Player):
    def __init__(self, world, player : Player):
        
        super().__init__(world, player.raw)

        self.last_seen : datetime.datetime = None
        self.total_online : int = 0

class World():
    def __init__(self):

        self.total_tracked : int = 0
        self.last_refreshed : datetime.datetime = None

        self.is_stormy = None
        self.is_thundering = None
        self.time = None
        
        self.players : typing.List[Player] = []
        self.nations : typing.List[Nation] = []
        self.cultures : typing.List[Culture] = []
        self.religions : typing.List[Religion] = []
        self.towns : typing.List[Town] = []

        self.version = VERSION
        self.loaded_old_data = False

        self.next_refresh : datetime.datetime = None
        self.process_time : datetime.timedelta = None

        

        #self._parse_data(data, map_data)

    @property 
    def online_players(self) -> typing.List[Player]:
        return [p for p in self.players if p.online]

    @property 
    def towns_future(self):
        return self.towns

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

    def get_player(self, name : str, case_sensitive = True, online=None):
        for player in self.players:
            if online == True and player.online == False or online == False and player.online == True:
                continue 

            if player.name == name or (not case_sensitive and player.name.lower() == name.lower()):
                return player 
        
        return None

    def get_town(self, name : str, case_sensitive = True):
        for town in self.towns:
            if town.name == name or (not case_sensitive and town.name.lower() == name.lower()):
                return town 

        return None    
    
    def get_nation(self, name : str, case_sensitive = True) -> Nation:
        for nation in self.nations:
            if nation.name == name or (not case_sensitive and nation.name.lower() == name.lower()):
                return nation 

        return None   
    
    def get_culture(self, name : str, case_sensitive = True) -> Culture:
        for culture in self.cultures:
            if culture.name == name or (not case_sensitive and culture.name.lower() == name.lower()):
                return culture 

        return None   
    
    def get_religion(self, name : str, case_sensitive = True) -> Religion:
        for religion in self.religions:
            if religion.name == name or (not case_sensitive and religion.name.lower() == name.lower()):
                return religion 

        return None   
    
    
    def load_old_world(self, old_world : dict):
        for attr_name, attr_value in old_world.items():
            if attr_name not in ["players", "towns", "nations", "cultures", "religions"]:
                setattr(self, attr_name, attr_value)
                
            else:
                for obj in attr_value:
                    
                    trs = {"players":Player, "towns":Town, "nations":Nation, "cultures":Culture, "religions":Religion}
                    t : typing.Type[typing.Union[Player, Town, Nation, Culture, Religion]] = trs[attr_name]
                    o = t.load_old(self, obj)
                    getattr(self, attr_name).append(o)

        


        

    
    def to_dict(self):

        return to_dict(self)
    
    

