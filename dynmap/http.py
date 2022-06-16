import aiohttp
import json

class HTTP():
    def __init__(self, client):
        self.client = client 
    
    async def request(self, method : str, path : str=None, data = None, url=None):

        async with aiohttp.ClientSession() as s:
            async with s.request(method, url=url or (self.client.url + path), data=data) as r:
                text = await r.text()
                
                try:
                    return json.loads(text)
                except:
                    pass
    
    request_async = request

    def request_sync(self, method : str, path : str, data = None):

        return self.client.loop.run_until_complete(self.request(method, path, data))
