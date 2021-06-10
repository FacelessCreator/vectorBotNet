import jsonWebsocket
import asyncio
import websockets
import threading
import json

class PipeGUIServer():
    def __init__(self, host, port):
        self.lastId = 1
        self.host = host
        self.port = port
        self.connections = dict()
        self.newGUIEvent = None
        self.lock = threading.Lock()
        main_thread = threading.Thread(target=self.mainLoop, args=(), daemon=True)
        main_thread.start()
    async def readingFunction(self):
        while True:
            await asyncio.sleep(0.001)
            self.lock.acquire()
            for id in self.connections:
                connection = self.connections[id]
                message = connection.get_last()
                if not message:
                    continue
                msg_type = message["type"]
                pass
            self.lock.release()
    async def newClientFunction(self, websocket, path):
        greetingStr = await websocket.recv()
        greeting = ""
        try:
            greeting = json.loads(greetingStr)
        except Exception as e:
            print(e)
            await websocket.send('{"type":"connect_answer", "code": 3}')
            return
        if not "type" in greeting or not greeting["type"] == "connect":
            await websocket.send('{"type":"connect_answer", "code": 1}')
            return
        await websocket.send('{"type":"connect_answer", "code": 0}')
        loop = asyncio.get_event_loop()
        jws = jsonWebsocket.JsonWebsocket(websocket)
        tasks = jws.add_asyncio_tasks(loop)
        self.lock.acquire()
        self.lastId += 1
        id = self.lastId
        self.connections[id] = jws
        if self.newGUIEvent:
            self.newGUIEvent(jws)
        self.lock.release()
        await asyncio.gather(*tasks)
        self.lock.acquire()
        self.connections.pop(id)
        self.lock.release()
    def mainLoop(self):
        ioloop = asyncio.new_event_loop()
        asyncio.set_event_loop(ioloop)
        start_server = websockets.serve(self.newClientFunction, self.host, self.port)
        ioloop.create_task(self.readingFunction())
        ioloop.run_until_complete(start_server)
        ioloop.run_forever()
        ioloop.close()
    def newClientEvent(self, name, vector_format, coefficients_format, GUI_format):
        self.lock.acquire()
        for id in self.connections:
            message = {"type": "new_client", "name":name, "vector_format":vector_format, "coefficients_format":coefficients_format}
            if GUI_format:
                message["GUI_format"] = GUI_format
            self.connections[id].send(message)
        self.lock.release()
    def lostClientEvent(self, name):
        self.lock.acquire()
        for id in self.connections:
            self.connections[id].send({"type": "lost_client", "name":name})
        self.lock.release()
    def newVectorEvent(self, name, t, vector):
        self.lock.acquire()
        for id in self.connections:
            self.connections[id].send({"type":"vector", "owner":name, "t":t, "vector":vector})
        self.lock.release()