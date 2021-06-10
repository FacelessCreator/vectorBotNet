import jsonWebsocket
import asyncio
import websockets
import threading
import json

class BotNetServer():
    def __init__(self, host, port):
        self.connections = dict()
        self.vector_formats = dict()
        self.coefficients_formats = dict()
        self.GUI_formats = dict()
        self.host = host
        self.port = port
        self.vectors = dict()
        self.lock = threading.Lock()
        self.newClientEvent = None
        self.lostClientEvent = None
        main_thread = threading.Thread(target=self.mainLoop, args=(), daemon=True)
        main_thread.start()
    async def readingFunction(self):
        while True:
            await asyncio.sleep(0.001)
            self.lock.acquire()
            for name in self.connections:
                connection = self.connections[name]
                message = connection.get_last()
                if not message:
                    continue
                msg_type = message["type"]
                if msg_type == "vector":
                    self.vectors[name].append((message["t"], message["vector"]))
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
        if not "vector_format" in greeting or not "coefficients_format" in greeting:
            await websocket.send('{"type":"connect_answer", "code": 4}')
            return
        if not "GUI_format" in greeting:
            GUI_format = Null
        else:
            GUI_format = greeting["GUI_format"]
        vector_format = greeting["vector_format"]
        coefficients_format = greeting["coefficients_format"]
        name = greeting["name"]
        if name in self.connections:
            await websocket.send('{"type":"connect_answer", "code": 2}')
            return
        await websocket.send('{"type":"connect_answer", "code": 0}')
        loop = asyncio.get_event_loop()
        jws = jsonWebsocket.JsonWebsocket(websocket)
        tasks = jws.add_asyncio_tasks(loop)
        self.lock.acquire()
        self.connections[name] = jws
        self.vector_formats[name] = vector_format
        self.coefficients_formats[name] = coefficients_format
        self.vectors[name] = []
        self.GUI_formats[name] = GUI_format
        if self.newClientEvent:
            self.newClientEvent(name, vector_format, coefficients_format, GUI_format)
        self.lock.release()
        await asyncio.gather(*tasks)
        self.lock.acquire()
        self.connections.pop(name)
        self.vector_formats.pop(name)
        self.coefficients_formats.pop(name)
        self.vectors.pop(name)
        self.GUI_formats.pop(name)
        if self.lostClientEvent:
            self.lostClientEvent(name)
        self.lock.release()
    def mainLoop(self):
        ioloop = asyncio.new_event_loop()
        asyncio.set_event_loop(ioloop)
        start_server = websockets.serve(self.newClientFunction, self.host, self.port)
        ioloop.create_task(self.readingFunction())
        ioloop.run_until_complete(start_server)
        ioloop.run_forever()
        ioloop.close()
    def getNames(self):
        self.lock.acquire()
        res = self.connections.keys()
        self.lock.release()
        return res
    def getFirstVector(self, name):
        res = (None, None)
        self.lock.acquire()
        if len(self.vectors[name]) > 0:
            res = self.vectors[name].pop(0)
        self.lock.release()
        return res
    def getLastVector(self, name):
        res = (None, None)
        self.lock.acquire()
        if len(self.vectors[name]) > 0:
            res = self.vectors[name].pop(-1)
        self.lock.release()
        return res
    def getVectorFormat(self, name):
        self.lock.acquire()
        res = self.vector_formats[name]
        self.lock.release()
        return res
    def getCoefficientsFormat(self, name):
        self.lock.acquire()
        res = self.coefficients_formats[name]
        self.lock.release()
        return res
    def getGUIFormat(self, name):
        self.lock.acquire()
        res = self.GUI_formats[name]
        self.lock.release()
        return res
    def sendVector(self, name, t, vector):
        self.lock.acquire()
        if name in self.connections:
            self.connections[name].send({"type": "vector", "t": t, "vector": vector})
        self.lock.release()
    def setControlling(self, name, mode):
        value = 0
        if mode:
            value = 1
        self.lock.acquire()
        if name in self.connections:
            self.connections[name].send({"type": "set_controlling", "value": value})
        self.lock.release()
    def setLogging(self, name, mode):
        value = 0
        if mode:
            value = 1
        self.lock.acquire()
        if name in self.connections:
            self.connections[name].send({"type": "set_logging", "value": value})
        self.lock.release()
    def setCoefficients(self, name, coefficients):
        self.lock.acquire()
        if name in self.connections:
            self.connections[name].send({"type": "set_coefficients", "value": coefficients})
        self.lock.release()
    def clear(self, name):
        self.lock.acquire()
        if name in self.connections:
            self.connections[name].send({"type": "clear"})
        self.lock.release()

class BotNetClient():
    def __init__(self, host, port, vector_format, coefficients_format, GUI_format, name):
        self.connection = None
        self.vectors = []
        self.host = host
        self.port = port
        self.vector_format = vector_format
        self.coefficients_format = coefficients_format
        self.GUI_format = GUI_format
        self.name = name

        self.isLogging = False
        self.isControlling = False
        self.setCoefficientsEvent = None
        self.clearEvent = None
        
        self.lock = threading.Lock()
        main_thread = threading.Thread(target=self.mainLoop, args=(), daemon=True)
        main_thread.start()
    def mainLoop(self):
        ioloop = asyncio.new_event_loop()
        asyncio.set_event_loop(ioloop)
        ioloop.run_until_complete(self.connect())
        if self.connection:
            print("success!")
            ioloop.create_task(self.readingFunction())
        ioloop.run_forever()
        ioloop.close()
    async def connect(self):
        uri = "ws://{}:{}".format(self.host, self.port)
        try:
            websocket = await websockets.connect(uri)
        except OSError as e:
            print(e)
            return
        message = {"type": "connect", "vector_format": self.vector_format, "coefficients_format": self.coefficients_format, "GUI_format": self.GUI_format, "name": self.name}
        messageStr = json.dumps(message)
        await websocket.send(messageStr)
        greetingStr = await websocket.recv()
        greeting = ""
        try:
            greeting = json.loads(greetingStr)
        except Exception as e:
            print(e)
            return
        if not "code" in greeting or greeting["code"] != 0:
            print(greeting)
            return
        loop = asyncio.get_event_loop()
        jws = jsonWebsocket.JsonWebsocket(websocket)
        tasks = jws.add_asyncio_tasks(loop)
        self.connection = jws
    async def readingFunction(self):
        while True:
            self.lock.acquire()
            message = self.connection.get_last()
            if not message:
                self.lock.release()
                await asyncio.sleep(0.001)
                continue
            msg_type = message["type"]
            if msg_type == "vector":
                self.vectors.append((message["t"], message["vector"]))
            elif msg_type == "set_logging":
                self.isLogging = message["value"] == 1
            elif msg_type == "set_controlling":
                self.isControlling = message["value"] == 1
            elif msg_type == "clear":
                if self.clearEvent:
                    self.clearEvent()
            elif msg_type == "set_coefficients":
                if self.setCoefficientsEvent:
                    self.setCoefficientsEvent(message["value"])
            self.lock.release()
    def getFirstVector(self):
        res = (None, None)
        self.lock.acquire()
        if len(self.vectors) > 0:
            res = self.vectors.pop(0)
        self.lock.release()
        return res
    def getLastVector(self):
        res = (None, None)
        self.lock.acquire()
        if len(self.vectors) > 0:
            res = self.vectors.pop(-1)
        self.lock.release()
        return res
    def isConnected(self):
        res = False
        self.lock.acquire()
        if self.connection and self.connection.is_connected():
            res = True
        self.lock.release()
        return res
    def sendVector(self, t, vector):
        self.lock.acquire()
        self.connection.send({"type": "vector", "t": t, "vector": vector})
        self.lock.release()
