import websockets
import asyncio
import json

class JsonWebsocket():
    def __init__(self, websocket):
        self.in_buffer = []
        self.out_buffer = []
        self.websocket = websocket
    async def send_function(self):
        while (self.websocket):
            if (len(self.out_buffer) == 0):
                await asyncio.sleep(0.01)
            else:
                message = self.out_buffer.pop(0)
                messageStr = json.dumps(message)
                await self.websocket.send(messageStr)
    async def recv_function(self):
        try:
            async for messageStr in self.websocket:
                try:
                    message = json.loads(messageStr)
                    self.in_buffer.append(message)
                except Exception:
                    pass
        except websockets.exceptions.ConnectionClosedError:
            pass
        self.websocket = None
    def add_asyncio_tasks(self, loop):
        tasks = [loop.create_task(self.send_function()), loop.create_task(self.recv_function())]
        return tasks
    def send(self, message):
        self.out_buffer.append(message)
    def get_last(self):
        if (len(self.in_buffer) == 0):
            return None
        else:
            return self.in_buffer.pop(0)
    def is_connected(self):
        return self.websocket != None