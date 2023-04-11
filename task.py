
from cogs import tasks 
import asyncio 
import setup as s 
import dynmap
import datetime

def periodic(cl : dynmap.Client):

    async def task():
        #cl = dynmap.Client(None, "https://map.rulercraft.com")

        while True:
            start_time = datetime.datetime.now()
            try:
                w = await tasks.refresh_file(cl)
                cl.world = w
            except Exception as e:
                print(e)

            if s.DEBUG_MODE: print("Loaded world!")
            
            await asyncio.sleep(s.REFRESH_INTERVAL - (datetime.datetime.now() - start_time).total_seconds())
    
    loop = asyncio.new_event_loop()
    loop.run_until_complete(task())