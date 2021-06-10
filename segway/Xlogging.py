import time
import defaults

class Logging ():

    def __init__(self):
        self.dict = defaults.getFullStatus()
        self.logs = []

    def save(self, path: str):
        saveFile = open(path, "w")
        for line in self.logs:
            save_line = " ".join(list(map(str, line))) + "\n"
            saveFile.write(save_line)
        saveFile.close()
        return len(self.logs)

    def clear(self):
        self.dict = defaults.getFullStatus()
        self.logs.clear()

    def last(self):
        return dict(self.dict)

    def add(self, new_dict: dict):
        self.dict = dict(new_dict)
        self.logs.append(new_dict.values())


if __name__ =='__main__':
    log = Logging()
    full_vector = log.last() 
    full_vector["psi"] = 32
    full_vector["t"] = 341
    full_vector["psi"] = 32
    full_vector["teta"] = -1
    t0 = time.time()
    for i in range(100000):
        log.add(full_vector)
    print((time.time()-t0)*1000)
    print(log.last())
    print()
    t0 = time.time()
    log.save("logs.txt")
    print((time.time()-t0)*1000)
    log.clear()
    print(log.dict, "\n", log.logs)
    