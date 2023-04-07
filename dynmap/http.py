import aiohttp
import json

class HTTP():
    def __init__(self, client):
        self.client = client 
        self.session = None
    
    async def request(self, method : str, path : str=None, data = None, url=None):

        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.request(method, url=url or (self.client.url + path), data=data) as r:
            text = await r.text()
            
            try:
                return json.loads(text)
            except:
                pass
    
    request_async = request
