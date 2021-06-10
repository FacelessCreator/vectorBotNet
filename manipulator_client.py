#from vectorBotNet.segway.segway_client import SIZE
from typing import Sized
from manipulator.geometry import anglesToCoords, coordsToAngles
from numpy import NaN
from botNet import *
import time
from manipulator.manipulator_motor import *
from manipulator.controller import PID
from math import pi, sqrt
import sys

IS_VIRTUAL = True
MOTORS_COUNT = 3

U_MAX = 8.3
km = 0.583
ke = 0.583
J = 0.0024
R = 8.4

SIZES = [1, 3, 5]

OUTPUT_NAMES = [1, 2, 3, 4]

class Manipulator():
    global IS_VIRTUAL, MOTORS_COUNT, U_MAX, km, ke, J, R, SIZES

    def __init__(self):
        self.start_time = time.time()
        self.motors = [VirtualMotor(U_MAX, km, ke, J, R) for i in range(MOTORS_COUNT)]
        self.controllers = [PID(0) for i in range(MOTORS_COUNT)]
        self.angles_target = [0]*MOTORS_COUNT
        self.angles_now = [0]*MOTORS_COUNT
        self.e = [a-b for a, b in zip(self.angles_target, self.angles_now)]

    def setPowers(self, power:list):
        for i in range(MOTORS_COUNT):
            self.motors[i].setPower(power[i])
           
    def moving(self, dt):
        powers = [controller.control(e, dt) for controller, e in zip(self.controllers, self.e)]
        for i in range(MOTORS_COUNT):
            self.motors[i].setPower(powers[i])
        self.update_angles()

    def update_angles(self):
        self.angles_now = [motor.getTeta() for motor in self.motors]
        self.e = [a-b for a, b in zip(self.angles_target, self.angles_now)]

    def set_target(self, target: list):
        x, y, z = target[:3]
        if not x is NaN :
            distance = sqrt(x**2+(y-SIZES[0])**2+z**2)
            if distance > SIZES[1]+SIZES[2] :
                print(f"Координаты {x, y, z} недопустимы для данных размеров робота.")
                return False
            angles = coordsToAngles([x, y, -z], SIZES)
        else:
            angles = target[3:]
        self.angles_target = angles
        self.update_angles()
        return True

    def virtual_tick(self, dt):
        for motor in self.motors:
            motor.tick(dt)

    def clearEvent(self):
        self.start_time = time.time()
        for motor, controler, e in zip(self.motors, self.controllers, self.e):
            motor.clear()
            controler.clear(e)
            self.angles_target = [0]*MOTORS_COUNT
            self.angles_now = [0]*MOTORS_COUNT
            self.e = [a-b for a, b in zip(self.angles_target, self.angles_now)]

    def setCoefficientsEvent(self, new_values:list):
        k = {"kp": new_values[0], "ki": new_values[1], "kd": new_values[2]}
        for controller in self.controllers:
            controller.setCoefficients(k)

    def getVector(self):
        vector = anglesToCoords(self.angles_now, SIZES) + self.angles_now
        return vector


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("wrong args; use HOST PORT CLIENT_NAME")
        exit()
    HOST = sys.argv[1]
    PORT = sys.argv[2]
    NAME = sys.argv[3]
    GUI_format = {"model": "manipulator", "a1":SIZES[0], "a2": SIZES[1], "a3": SIZES[2]}
    try:
        connection = BotNetClient(HOST, PORT, ["x", "y", "z", "teta1", "teta2", "teta3"], ["kp", "ki", "kd"], GUI_format, NAME)
    except Exception as e:
        print("Ошибка соединения")
        print(e)
        exit()
    robot = Manipulator()
    connection.clearEvent = robot.clearEvent
    connection.setCoefficientsEvent = robot.setCoefficientsEvent
    connection.isControlling = True
    connection.isLogging = True

    start_time = robot.start_time
    time_now = 0 
    time.sleep(3) # wait for connection
    while connection.isConnected():
        dt = time.time() - robot.start_time - time_now
        time_now += dt
        if connection.isControlling:
            if sum(robot.e) < (15/180*pi) and connection.vectors:
                t, new_target = connection.getFirstVector()
                robot.set_target(new_target)
            robot.moving(dt)
        if connection.isLogging:
            vector = robot.getVector()
            connection.sendVector(time_now, vector)
        if IS_VIRTUAL:
            robot.virtual_tick(dt)
            time.sleep(0.01)

    robot.clearEvent()
    print("Подключение разорвано")