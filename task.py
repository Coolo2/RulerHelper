
from cogs import tasks 
import asyncio 
import setup as s 
import dynmap
import sys
import datetime

async def periodic():
    cl = dynmap.Client(None, "https://map.rulercraft.com")
    while True:
        start_time = datetime.datetime.now()
        try:
            await tasks.refresh_file(cl)
        except Exception as e:
            print(e)
        await asyncio.sleep(s.REFRESH_INTERVAL - (datetime.datetime.now() - start_time).total_seconds())

if "thread" in sys.argv:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    task = loop.create_task(periodic())

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass