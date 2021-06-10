

class Physics():
    def __init__(self):
        self.status = {
            't' : 0,
            'psi' : 0,
            'dpsi' : 0,
            'tetaL' : 0,
            'tetaR' : 0
        }

    def setRegulation(self, power_vector):
        pass

    def getStatus(self):
        return dict(self.status)

    def clear(self):
        pass