from vectorBotNet.segway.virtualPhysics import VirtualPhysics2
import botNet
import time
from segway.motor import *
from segway.regulator import *
from math import pi
import sys
import segway.defaults
import numpy as np

class Segway():
    def __init__(self):
        self.coeffs = defaults.getCoeffs()
        self.target = defaults.getTarget()
        self.physics = VirtualPhysics2(self.coeffs, np.array([[0.01],[0],[0]]))


    def moving():
        pass
        
















if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("wrong args; use HOST PORT CLIENT_NAME SIZE")
        exit()
    HOST = sys.argv[1]
    PORT = sys.argv[2]
    NAME = sys.argv[3]
    SIZE = sys.argv[4]
    GUI_format = {{"model": "segway", "size": SIZE}}
    try:
        connection = botNet.BotNetClient(HOST, PORT, ["x","z","psi"], ["KteetaT", "psiMax", "Krot", "rotMax", "tp"], GUI_format, NAME)
    except Exception as e:
        print("Ошибка соединения")
        print(e)
        exit()
    robot = Segway()
    connection.clearEvent = robot.clearEvent
    connection.setCoefficientsEvent = robot.setCoefficientsEvent

    start_time = time.time()
    time_now = 0 
    time.sleep(1) # wait for connection
    while connection.isConnected():
        dt = time.time() - start_time - time_now
        time_now += dt
        if connection.isControlling:
            if sum(robot.e) < (15/180*pi) and connection.vectors:
                t, new_target = connection.getFirstVector()
                robot.set_target(new_target)
            robot.moving(dt)
        if connection.isLogging:
            vector = robot.angles_now
            connection.sendVector(time_now, vector)
        if IS_VIRTUAL:
            robot.virtual_tick(dt)
            time.sleep(0.01)

    robot.clearEvent()
    print("Подключение разорвано")