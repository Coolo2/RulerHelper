
from cogs import tasks 
import asyncio 
import setup as s 
import dynmap
import sys
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
            
            await tasks.notifications(cl.bot, cl)
            await tasks.refresh_status(cl.bot, cl)

            if s.DEBUG_MODE: print("Loaded world!")
            
            await asyncio.sleep(s.REFRESH_INTERVAL - (datetime.datetime.now() - start_time).total_seconds())
    
    loop = asyncio.new_event_loop()
    loop.run_until_complete(task())

if "thread" in sys.argv:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    task = loop.create_task(periodic())

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass