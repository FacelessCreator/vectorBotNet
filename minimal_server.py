import botNet
import time

if __name__ == "__main__":
    botNetServer = botNet.BotNetServer("0.0.0.0", 8080)
    while True:
        time.sleep(1)
        names = botNetServer.getNames()
        for name in names:
            botNetServer.sendVector(name, time.time(), [55555])