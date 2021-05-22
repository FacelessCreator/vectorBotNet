import botNet
import time

if __name__ == "__main__":
    connection = botNet.BotNetClient("localhost", 8080, ["teta"], ["k"], "tester")
    time.sleep(1)
    while connection.isConnected():
        time.sleep(1)
        connection.sendVector(time.time(), [1])