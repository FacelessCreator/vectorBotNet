import botNet
import time
from motor import *
from controller import PID
from math import pi
import sys

IS_VIRTUAL = True
MOTORS_COUNT = 3

U_MAX = 8.3
km = 0.583
ke = 0.583
J = 0.0024
R = 8.4

if not IS_VIRTUAL:
    #import from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    OUTPUT_NAMES = [OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D]
else:
    OUTPUT_NAMES = [1, 2, 3, 4]

class Manipulator():
    global IS_VIRTUAL, MOTORS_COUNT, U_MAX, km, ke, J, R

    def __init__(self) -> None:
        if IS_VIRTUAL:
            self.motors = [VirtualMotor(U_MAX, km, ke, J, R) for i in range(MOTORS_COUNT)]
        else: 
            self.motors = [RealMotor(OUTPUT_NAMES[i]) for i in range(MOTORS_COUNT)]
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

    def set_target(self, target_angles: list):
        self.angles_target = target_angles
        self.update_angles()

    def virtual_tick(self, dt):
        for motor in self.motors:
            motor.tick(dt)

    def clearEvent(self):
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


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("wrong args; use HOST PORT CLIENT_NAME")
        exit()
    HOST = sys.argv[1]
    PORT = sys.argv[2]
    NAME = sys.argv[3]
    try:
        connection = botNet.BotNetClient(HOST, PORT, ["teta1", "teta2", "teta3"], ["kp", "ki", "kd"], NAME)
    except Exception as e:
        print("Ошибка соединения")
        print(e)
        exit()
    robot = Manipulator()
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