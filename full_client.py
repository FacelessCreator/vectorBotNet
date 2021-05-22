import time
import sys

import botNet

def clearFunction():
    print("clear event!")

def setCoefficientsFunction(coefficients):
    print("new coefficients {}".format(coefficients))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("wrong args; use HOST PORT CLIENT_NAME")
        exit()
    HOST = sys.argv[1]
    PORT = sys.argv[2]
    CLIENT_NAME = sys.argv[3]

    connection = botNet.BotNetClient(HOST, PORT, ["teta"], ["k"], CLIENT_NAME)
    time.sleep(1)
    if not connection.isConnected():
        print("no connection")
        exit()
    connection.clearEvent = clearFunction
    connection.setCoefficientsEvent = setCoefficientsFunction
    i = 0
    while connection.isConnected():
        time.sleep(0.2)
        i+= 1
        if i >= 5:
            i = 0
            connection.sendVector(time.time(), [1])
        t, vect = connection.getLastVector()
        if t:
            print("{}: {}".format(t, vect))
        