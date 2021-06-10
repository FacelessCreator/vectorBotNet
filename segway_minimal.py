import json
import time
import numpy as np
import sys

import botNet
from math import cos, sin, copysign, pi, sqrt, atan2

r = 0.028 # радиус колеса
lbw = 0.072 # ширина со стороны дисплея
lbh = 0.110 # высота блока
lbt = 0.052 # толщина блока
mt = 0.282 # масса блока
mk = 0.020 # масса колеса
l =  0.092 # расстояние между центром колёс и центром блока
Jt = 1/12 * mt * (lbh**2 + lbt**2) + mt*l**2 # момент инерции блока 
Jk = 0.5 * mk * r**2 # момент инерции колеса
J = 0.0024 # момент инерции ротора
ke = 0.583
km = 0.583
R = 8.4
g = 9.81
Bw = 0.184 # расстояние между центрами колёс
Umax = 8.3
tp_standart = 6.3 # «стандартное» значение времени переходного процесса

dt = 0.0002

q = np.array([[0.1], [0], [0]]) # psi tetaL tetaR
q1 = np.array([[0], [0], [0]]) # psi1 tetaL1 tetaR1
U = np.array([[0], [0]]) # UL UR
t = 0

xT = 0
yT = 0
ex = 0
ey = 0
ro = 0
alpha = 0
tetaT = 0

KtetaT = 0.02
psiMax = 0.1
Krot = 50
rotMax = 100
tp = 2

new_teta = 0
teta = 0
teta1 = 0
beta = 0
beta1 = 0
xl = 0
xl1 = 0
x = 0
x1 = 0
y = 0
y1 = 0

A = np.array([[Jt+mt*l*l, -0.5*mt*r*l+J, -0.5*mt*r*l+J], [0.5*mt*r*l, Jk+J+0.5*mk*r*r+0.25*mt*r*r, J+0.5*mk*r*r+0.25*mt*r*r], [0.5*mt*r*l, J+0.5*mk*r*r+0.25*mt*r*r, Jk+J+0.5*mk*r*r+0.25*mt*r*r]])
B = np.array([[0, km*ke/R, km*ke/R], [0, km*ke/R, 0], [0, 0, km*ke/R]])
C = np.array([[-mt*g*l, 0, 0], [0, 0, 0], [0, 0, 0]])
H = np.array([[-km/R, -km/R], [km/R, 0], [0, km/R]])
D = -np.linalg.inv(A).dot(B)
E = -np.linalg.inv(A).dot(C)
F = np.linalg.inv(A).dot(H)

def getAkkermanCoefficients():

    # Вспомогательный коэффициент
    kappa = mt*l*r*(mt * l * r - 2*J) - (mt* l**2 + Jt) * (mt*r**2 + 2*mk*r**2 + 2*Jk + 2*J)

    #создание матрицы А
    a21 = mt**2 * g * l**2 * r / kappa
    a22 = 2*ke*km * (mt*l*r + mt*l**2 + Jt) / (R*kappa)
    a31 = - mt*g*l*(mt*r**2 + 2*mk*r**2 + 2*Jk + 2*J) / kappa
    a32 = - 2*ke*km * (mt*l*r + mt*r**2 + 2*mk*r**2 + 2*Jk) / (R*kappa)
    A = np.array([[0, 0, 1], [a21, a22, 0], [a31, a32, 0]])
    #print(A)
    
    #создание матрицы В
    b21 = - 2*km*(mt*l*r + mt*l**2 + Jt) / (R*kappa)
    b31 = 2*km*(mt*l*r + mt*r**2 + 2*mk*r**2 + 2 *Jk) / (R*kappa)
    B =  np.array([[0, b21, b31]]).transpose()
    #print(B)

    #создание матрицы Y
    AB = A.dot(B)
    AAB = A.dot(A.dot(B))
    Y = np.concatenate((B, AB, AAB), axis = 1)
    #print(Y)

    #создание матрицы f(A)
    omega = tp_standart / tp
    z2 = 3*omega
    z1 = 3*omega**2
    z0 = omega**3
    f = A.dot(A).dot(A) + z2*( A.dot(A) ) + z1*A + z0*np.eye(3)
    #print(f)

    #финальная матрица K
    K = np.array([[0, 0, 1]]).dot( np.linalg.inv(Y)).dot(f)
    K = K * (100 / Umax)

    return K

K = getAkkermanCoefficients()

def tickPhysics(dt):
    global q, q1, t, D, E, F
    q2 = D.dot(q1) + E.dot(q) + F.dot(U)
    q1 = q1 + q2*dt
    q = q + q1*dt
    t += dt

def regulate(dt):
    global q, q1, K, U, Umax, new_teta, teta, teta1, beta, beta1, xl, xl1, x, x1, y, y1, ex, ey, ro, alpha, tetaT
    new_teta = (q[1][0] + q[2][0]) / 2
    teta1 = (new_teta - teta) / dt
    teta = new_teta
    xl1 = teta1 * r * 100
    xl += xl1 * dt
    beta1 = r/Bw * (q1[2][0] - q1[1][0])
    beta += beta1 * dt
    x1 = cos(beta) * xl1
    y1 = sin(beta) * xl1
    x += x1 * dt
    y += y1 * dt
    ex = xT-x
    ey = yT-y
    gamma = atan2(ey, ex)
    alpha = gamma - beta # угол ошибки
    if (abs(alpha) > pi): # не забываем про выход за границы множества углов [-pi; pi)
        alpha = alpha - copysign(1, alpha) * 2 * pi
    ro = sqrt(ey**2 + ex**2)
    tetaT = teta + ro * cos(alpha) / r

    perfectPsi = 0
    perfectPsi1 = 0
    perfectTeta1 = 0

    perfectPsi = tetaT * KtetaT
    if (abs(perfectPsi) > psiMax):
        perfectPsi = copysign(1, perfectPsi) * psiMax
    rot = alpha * Krot
    if (abs(rot) > rotMax):
        rot = copysign(1, rot) * rotMax

    X = np.array([[q[0][0]], [teta1], [q1[0][0]]])
    perfectX = np.array([[perfectPsi], [perfectTeta1], [perfectPsi1]])
    e = perfectX - X
    Pmiddle = K.dot(e)[0][0]
    P = np.array([[Pmiddle - rot], [Pmiddle + rot]])
    U = P / 100 * Umax
    if (abs(U[0][0]) > Umax):
        U[0][0] = copysign(1, U[0][0]) * Umax
    if (abs(U[1][0]) > Umax):
        U[1][0] = copysign(1, U[1][0]) * Umax

def clearFunction():
    q = np.array([[0], [0], [0]]) # psi tetaL tetaR
    q1 = np.array([[0], [0], [0]]) # psi1 tetaL1 tetaR1
    U = np.array([[0], [0]]) # UL UR
    t = 0

def setCoefficientsFunction(coefficients):
    KtetaT = coefficients[0]
    psiMax = coefficients[1]
    Krot = coefficients[2]
    rotMax = coefficients[3]
    tp = coefficients[4]

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
        tickPhysics(dt)
        count += 1
        if (count % 1 == 0): #and (connection.isControlling):
            new_t, new_vect = connection.getLastVector()
            if new_vect:
                xT = new_vect[0]
                yT = new_vect[1]
            regulate(dt*1)
        if (count % 200 == 0): #and (connection.isLogging):
            connection.sendVector(time.time(), [x, y, beta, q[0][0]])
        time.sleep(dt)
