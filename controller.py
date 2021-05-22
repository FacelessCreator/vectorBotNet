import math

class PID():
    def __init__(self, value):
        self.coefficients = {
            "kp": 0,
            "ki": 0,
            "kd": 0
        }
        self.last_value = value
        self.integral = 0
    def control(self, value, dt):
        value1 = (value - self.last_value) / dt
        self.last_value = value
        self.integral += value * dt
        return self.coefficients["kp"] * value + self.coefficients["ki"] * self.integral + self.coefficients["kd"] * value1
    def setCoefficients(self, new_coeffs: dict):
        self.coefficients = dict(new_coeffs)
    def clear(self, value):
        self.last_value = value
        self.integral = 0