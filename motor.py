import math

class Motor():
    def __init__(self):
        pass
    def getTeta(self):
        return 0
    def setPower(self, power):
        pass
    def clear(self):
        pass

class RealMotor (Motor):
    def __init__(self, inputName: str):
        from ev3dev2.motor import LargeMotor
        self.obj = LargeMotor(inputName)
        self.obj.position = 0
        self.tetaStart = self.obj.position
    def getTeta(self):
        return self.obj.position - self.tetaStart
    def setPower(self, power):
        self.obj.run_direct(duty_cycle_sp=(power))
    def clear(self):
        self.obj.position = 0
        self.tetaStart = self.obj.position
        self.obj.run_direct(duty_cycle_sp=(0))

class VirtualMotor (Motor):
    def __init__(self, U_MAX, km, ke, J, R):
        self.teta = 0
        self.teta1 = 0
        self.U = 0
        self.Umax = U_MAX
        self.km = km
        self.ke = ke
        self.J = J
        self.R = R
    def getTeta(self):
        return self.teta
    def setPower(self, power):
        self.U = power / 100 * self.Umax
        if (abs(self.U) > self.Umax):
            self.U = self.Umax * math.copysign(1, self.U)
    def tick(self, dt):
        teta2 = (self.U*self.km - self.teta1*self.km*self.ke) * (1/(self.J*self.R))
        self.teta1 += teta2*dt
        self.teta += self.teta1*dt
    def clear(self):
        self.teta = 0
        self.omega = 0
        self.U = 0