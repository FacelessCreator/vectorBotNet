import time
import sys
import os
import math
import numpy as np
from physics import Physics
from math import sin, cos

class VirtualPhysics(Physics):
    def __init__(self, consts: dict, q):
        mt = consts["mb"]
        mk = consts["mw"]
        l =  consts["l"]
        Jt = consts["Jb"]
        Jk = consts["Jw"]
        J = consts["J"]
        r = consts["r"]
        ke = consts["ke"]
        km = consts["km"]
        R = consts["R"]
        g = consts["g"]
        A = np.array([[Jt+mt*l*l, -0.5*mt*r*l+J, -0.5*mt*r*l+J], [0.5*mt*r*l, Jk+J+0.5*mk*r*r+0.25*mt*r*r, J+0.5*mk*r*r+0.25*mt*r*r], [0.5*mt*r*l, J+0.5*mk*r*r+0.25*mt*r*r, Jk+J+0.5*mk*r*r+0.25*mt*r*r]])
        B = np.array([[0, km*ke/R, km*ke/R], [0, km*ke/R, 0], [0, 0, km*ke/R]])
        C = np.array([[-mt*g*l, 0, 0], [0, 0, 0], [0, 0, 0]])
        self.qdefault = q
        H = np.array([[-km/R, -km/R], [km/R, 0], [0, km/R]])
        self.D = -np.linalg.inv(A).dot(B)
        self.E = -np.linalg.inv(A).dot(C)
        self.F = np.linalg.inv(A).dot(H)
        self.q = self.qdefault
        self.q1 = np.array([[0], [0], [0]])
        self.U = np.array([[0], [0]])
        self.Umax = consts["Umax"]
        self.t = 0
    
    def emulate(self, dt):
        q2 = self.D.dot(self.q1) + self.E.dot(self.q) + self.F.dot(self.U)
        self.q1 = self.q1 + q2*dt
        self.q = self.q + self.q1*dt
        self.t += dt

    def setRegulation(self, power_vector):
        if (abs(power_vector["PL"]) > 100):
            power_vector["PL"] = math.copysign(1, power_vector["PL"]) * 100
        if (abs(power_vector["PR"]) > 100):
            power_vector["PR"] = math.copysign(1, power_vector["PR"]) * 100
        self.U = np.array([[power_vector["PL"]], [power_vector["PR"]]]) * self.Umax*0.01
    
    def getStatus(self):
        status = {
            't' : self.t,
            'psi' : self.q[0][0],
            'psi1' : self.q1[0][0],
            'tetaL' : self.q[1][0],
            'tetaR' : self.q[2][0]
        }
        return status

    def clear(self):
        self.q = self.qdefault
        self.q1 = np.array([[0], [0], [0]])
        self.U = np.array([[0], [0]])
        self.t = 0


class VirtualPhysics2(Physics):
    def __init__(self, consts: dict, q):
        self.consts = dict(consts)
        self.qdefault = q
        self.q = self.qdefault
        self.q1 = np.array([[0], [0], [0]])
        self.U = np.array([[0], [0]])
        self.Umax = consts["Umax"]
        self.t = 0
    
    def emulate(self, dt):
        mt = self.consts["mb"]
        mk = self.consts["mw"]
        l =  self.consts["l"]
        Jt = self.consts["Jb"]
        Jk = self.consts["Jw"]
        J = self.consts["J"]
        r = self.consts["r"]
        ke = self.consts["ke"]
        km = self.consts["km"]
        R = self.consts["R"]
        g = self.consts["g"]
        q = self.q # psi tetaL tetaR
        q1 = self.q1 # psi1 tetaL1 tetaR1
        U = self.U # UL UR
        a00 = Jt + mt*l**2
        a01 = - mt*l*r*cos(q[0][0])/2 + J
        a02 = - mt*l*r*cos(q[0][0])/2 + J
        b0 = mt*g*l*sin(q[0][0]) - km*(U[0][0]+U[1][0])/R - km*ke/R*(q1[1][0]+q1[2][0])
        a10 = mt*l*r*cos(q[0][0])/2
        a11 = Jk + J + mk*r**2/2 + mt*r**2/4
        a12 = J + mk*r**2/2 + mt*r**2/4
        b1 = km*U[0][0]/R - km*ke/R*q1[1][0] + mt*l*r*q1[0][0]**2*sin(q[0][0])/2
        a20 = mt*l*r*cos(q[0][0])/2
        a21 = J + mk*r**2/2 + mt*r**2/4
        a22 = Jk + J + mk*r**2/2 + mt*r**2/4
        b2 = km*U[1][0]/R - km*ke/R*q1[2][0] + mt*l*r*q1[0][0]**2*sin(q[0][0])/2
        A = np.array([[a00, a01, a02], [a10, a11, a12], [a20, a21, a22]])
        B = np.array([[b0],[b1],[b2]])
        q2 = np.linalg.inv(A).dot(B)
        self.q1 = q1 + q2*dt
        self.q = q + q1*dt
        #if (abs(self.q[0][0]) > math.pi/2):
        #    self.q[0][0] = math.copysign(1, self.q[0][0]) * math.pi/2
        self.t += dt

    def setRegulation(self, power_vector):
        if (abs(power_vector["PL"]) > 100):
            power_vector["PL"] = math.copysign(1, power_vector["PL"]) * 100
        if (abs(power_vector["PR"]) > 100):
            power_vector["PR"] = math.copysign(1, power_vector["PR"]) * 100
        self.U = np.array([[power_vector["PL"]], [power_vector["PR"]]]) * self.Umax*0.01
    
    def getStatus(self):
        status = {
            't' : self.t,
            'psi' : self.q[0][0],
            'psi1' : self.q1[0][0],
            'tetaL' : self.q[1][0],
            'tetaR' : self.q[2][0]
        }
        return status

    def clear(self):
        self.q = self.qdefault
        self.q1 = np.array([[0], [0], [0]])
        self.U = np.array([[0], [0]])
        self.t = 0
