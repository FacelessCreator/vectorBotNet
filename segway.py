import json
import time
import numpy as np

import sys
sys.path.insert(1, 'build 3/segway')

from physics import Physics
import defaults
from selfControlFunction import selfControlFunction
from Xlogging import Logging

from virtualPhysics import *
from regulator import *

import botNet

logging = Logging()

coeffs = defaults.getCoeffs()
target = defaults.getTarget()
physics = VirtualPhysics2(coeffs, np.array([[0.1],[0],[0]]))

#regulator = Regulator()

#regulator = LinearProportionalRegulator()
#regulator.setCoefficients({"Kpsi": 10000,"Kpsi1":1000,"KtetaT":0.01,"psiMax":0.5,"Krot": 1000,"rotMax": 1000})

#regulator = AkkermanProportionalRegulator()
#regulator.setCoefficients({"tp":1, "perfectPsi":0, "perfectPsi1":0, "perfectTeta1":0})

regulator = HybridProportionalRegulator()
regulator.setCoefficients({"KtetaT":0.01, "psiMax":0.3, "Krot":50, "rotMax":100, "tp":2})

def clearFunction():
    physics.clear()
    logging.clear()

def setCoefficientsFunction(coefficients):
    regulator.setCoefficients(coefficients)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("wrong args; use HOST PORT CLIENT_NAME")
        exit()
    HOST = sys.argv[1]
    PORT = sys.argv[2]
    CLIENT_NAME = sys.argv[3]

    connection = botNet.BotNetClient(HOST, PORT, ["x", "z", "beta", "psi"], ["KtetaT","psiMax","Krot","rotMax","tp"], {"model": "segway", "size": 1}, CLIENT_NAME)
    time.sleep(1)
    if not connection.isConnected():
        print("no connection")
        exit()
    connection.clearEvent = clearFunction
    connection.setCoefficientsEvent = setCoefficientsFunction
    count = 0
    while connection.isConnected():
        physics.emulate(0.0001)
        count += 1
        if (count % 100 == 0) and (connection.isControlling):
            new_t, new_vect = connection.getLastVector()
            if new_vect:
                target["xT"] = new_vect[0]
                target["yT"] = new_vect[1]
            selfControlFunction(physics, logging, regulator, coeffs, target)
        if (count % 200 == 0) and (connection.isLogging):
            vect = logging.last()
            connection.sendVector(time.time(), [vect["x"], vect["y"], vect["beta"], vect["psi"]])
        time.sleep(0.0001)
