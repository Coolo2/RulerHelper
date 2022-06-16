

import asyncio, nest_asyncio

from dynmap import http
from dynmap import world
from dynmap import tracking

import typing

class Client():
    def __init__(self, bot, url : str):
        self.url = url

        self.loop = asyncio.get_event_loop()
        nest_asyncio.apply(self.loop)

        self.bot = bot

        self.http : http.HTTP = http.HTTP(self)

        self.cached_worlds : typing.Dict({str:world.World}) = {}
    
    async def get_world(self, name : str) -> world.World:

        import cogs.tasks

        data = await self.http.request("GET", path=f"/up/world/{name}/0")
        map_data = await self.http.request("GET", path=f"/tiles/_markers_/marker_{name}.json")

        if data == None or map_data == None:
            cogs.tasks.get_world_task(self.bot, self).stop()
            #cogs.tasks.get_world_task_no_processing(self.bot, self).stop()

            cogs.tasks.get_world_task(self.bot, self).start()
            #cogs.tasks.get_world_task_no_processing(self.bot, self).start()

        wd = world.World(self, data, map_data)

        self.cached_worlds[name] = wd

        return wd
    
    def get_tracking(self):

        return tracking.Tracking(self)
    
    get_world_async = get_world

    def get_world_sync(self, name : str) -> world.World:
        return self.loop.run_until_complete(self.get_world(name))
    
    
