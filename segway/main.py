import json
import time
import threading
import asyncio
import websockets
from concurrent.futures import FIRST_COMPLETED

from Xlogging import Logging
from physics import Physics
from regulator import Regulator
import defaults
from selfControlFunction import selfControlFunction

from virtualPhysics import *
from regulator import *
import numpy as np


def selfControlThreadFunction():
    global commandToController, messagesToWSclients
    logging = Logging()
    
    regulator = Regulator()

    #regulator = LinearProportionalRegulator()
    #regulator.setCoefficients({"Kpsi": 10000,"Kpsi1":1000,"KtetaT":0.01,"psiMax":0.5,"Krot": 1000,"rotMax": 1000})
    
    #regulator = AkkermanProportionalRegulator()
    #regulator.setCoefficients({"tp":1, "perfectPsi":0, "perfectPsi1":0, "perfectTeta1":0})

    regulator = HybridProportionalRegulator()
    regulator.setCoefficients({"KtetaT":0.01, "psiMax":0.3, "Krot":50, "rotMax":100, "tp":2})

    coeffs = defaults.getCoeffs()
    target = defaults.getTarget()
    physics = VirtualPhysics2(coeffs, np.array([[0.01],[0],[0]]))
    
    command = commandToController

    isRunning = False

    count = 0
    while (True):
        
        if (len(command) != 0):
            if (command["name"] == "exit"):
                exit()
            elif (command["name"] == "status"):
                msg = {"type": "status", "content": logging.last()}
                messagesToWSclients.append(msg)
            elif (command["name"] == "savelog"):
                linesCount = logging.save(command["path"])
                msg = {"type": "message", "content": "{} lines written into {}".format(linesCount, command["path"])}
                messagesToWSclients.append(msg)
            elif (command["name"] == "settarget"):
                target["xT"] = command["xT"]
                target["yT"] = command["yT"]
                msg = {"type": "message", "content": "new target {} {}".format(target["xT"], target["yT"])}
                messagesToWSclients.append(msg)
            elif (command["name"] == "start"):
                isRunning = True
            elif (command["name"] == "stop"):
                isRunning = False
            elif (command["name"] == "clear"):
                logging.clear()
                physics.clear()
                isRunning = False
            elif (command["name"] == "setregulatork"):
                command.pop("name")
                regulator.setCoefficients(command)
                msg = {"type": "message", "content": "regulator changed to {}".format(command)}
                messagesToWSclients.append(msg)
            
            command.clear()
        
        if (isRunning):
            physics.emulate(0.0001)
            count += 1
            if (count % 100 == 0):
                selfControlFunction(physics, logging, regulator, coeffs, target)
            if (count % 200 == 0):
                msg = {"type": "status", "content": logging.last()}
                messagesToWSclients.append(msg)

        time.sleep(0.0001)


async def websocketClientFunction(websocket, path):
    global WSclients, commandToController
    WSclients.append(websocket)
    async for command in websocket:
        try:
            commandAsDict = json.loads(command)
            commandToController.clear()
            commandToController.update(commandAsDict)
        except Exception:
            pass
        
    WSclients.remove(websocket)


async def websocketSendFunction():
    global WSclients, messagesToWSclients
    while (True):
        if (len(messagesToWSclients) == 0):
            await asyncio.sleep(0.1)
        else:
            message = messagesToWSclients.pop(0)
            messageStr = json.dumps(message)
            for client in WSclients:
                await client.send(messageStr)


async def multiThreadWaiter():
    global commandToController
    selfControlThread = threading.Thread(target=selfControlThreadFunction, args=())
    selfControlThread.start()
    while (selfControlThread.is_alive()):
        await asyncio.sleep(0.1)


WSclients = []
messagesToWSclients = []
commandToController = dict()

if __name__ =='__main__':
    start_server = websockets.serve(websocketClientFunction, "0.0.0.0", 8080)
    
    ioloop = asyncio.get_event_loop()
    tasks = [ioloop.create_task(websocketSendFunction()), ioloop.create_task(multiThreadWaiter())]
    wait_tasks = asyncio.wait(tasks, return_when=FIRST_COMPLETED)
    ioloop.run_until_complete(start_server)
    ioloop.run_until_complete(wait_tasks)
    for task in tasks:
        task.cancel()

    ioloop.close()