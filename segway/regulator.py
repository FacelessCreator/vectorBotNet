import math
import numpy as np
import defaults

class Regulator():
    def __init__(self):
        self.coefficients = {
            # Что-то есть
        }
        self.power_vector = {
            "PL" : 0,
            "PR" : 0
        }

    def regulate(self, full_state_vector: dict):
        self.power_vector["PL"] = 0 
        self.power_vector["PR"] = 0 
        return dict(self.power_vector)

    def setCoefficients(self, new_coeffs: dict):
        self.coefficients = dict(new_coeffs)


class LinearProportionalRegulator():
    def __init__(self):
        self.k = {
            "Kpsi": 0,
            "Kpsi1": 0,
            "KtetaT": 0,
            "psiMax": 0,
            "Krot": 0,
            "rotMax": 0
        }
    def regulate(self, fst: dict):
        psiPerfect = fst["tetaT"] * self.k["KtetaT"]
        if (abs(psiPerfect) > self.k["psiMax"]):
            psiPerfect = math.copysign(1, psiPerfect) * self.k["psiMax"]
        rot = fst["alpha"] * self.k["Krot"]
        if (abs(rot) > self.k["rotMax"]):
            rot = math.copysign(1, rot) * self.k["rotMax"]
        P = {
            "PL" : (fst["psi"] - psiPerfect)*self.k["Kpsi"] + fst["psi1"]*self.k["Kpsi1"] - rot,
            "PR" : (fst["psi"] - psiPerfect)*self.k["Kpsi"] + fst["psi1"]*self.k["Kpsi1"] + rot
        }
        return P
    def setCoefficients(self, new_coeffs: dict):
        self.k = dict(new_coeffs)

def getAkkermanCoefficients(tp, const:dict):
    c = const.copy()
    r = c["r"] 
    B = c["B"]
    mt = c["mb"] 
    mk = c["mw"] 
    l = c["l"]
    lbw = c["lbw"] # ширина со стороны дисплея
    lbh = c["lbh"] # высота блока
    lbt = c["lbt"] # толщина блока
    J = c["J"] # момент инерции ротора
    km = c["km"]
    ke = c["ke"]
    R = c["R"]
    g = c["g"]
    Jk = c["Jw"]
    Jt = c["Jb"]
    tp_standart = c["tp_standart"]
    Umax = c["Umax"]

    # Вспомогательный коэффициент
    kappa = mt*l*r*(mt * l * r - 2*J) \
        - (mt* l**2 + Jt) * (mt*r**2 + 2*mk*r**2 + 2*Jk + 2*J)

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

class AkkermanProportionalRegulator():
    def __init__(self):
        self.settings = {
            "tp": 1,
            "perfectPsi": 0,
            "perfectPsi1": 0,
            "perfectTeta1": 0
        }
        self.K = getAkkermanCoefficients(self.settings["tp"], defaults.getCoeffs())
    def regulate(self, fst: dict):
        x = np.array([[fst["psi"]], [fst["teta1"]], [fst["psi1"]]])
        perfectX = np.array([[self.settings["perfectPsi"]], [self.settings["perfectTeta1"]], [self.settings["perfectPsi1"]]])
        e = perfectX - x
        u = self.K.dot(e)[0][0]
        P = {
            "PL" : u,
            "PR" : u
        }
        return P
    def setCoefficients(self, settings: dict, recalcK=True):
        self.settings = dict(settings)
        if recalcK:
            self.K = getAkkermanCoefficients(self.settings["tp"], defaults.getCoeffs())

class HybridProportionalRegulator():
    def __init__(self):
        self.k = {
            "KtetaT": 0,
            "psiMax": 0,
            "Krot": 0,
            "rotMax": 0,
            "tp": 1
        }
        self.akkermanRegulator = AkkermanProportionalRegulator()
    def regulate(self, fst: dict):
        psiPerfect = fst["tetaT"] * self.k["KtetaT"]
        if (abs(psiPerfect) > self.k["psiMax"]):
            psiPerfect = math.copysign(1, psiPerfect) * self.k["psiMax"]
        rot = fst["alpha"] * self.k["Krot"]
        if (abs(rot) > self.k["rotMax"]):
            rot = math.copysign(1, rot) * self.k["rotMax"]
        self.k["perfectPsi"] = psiPerfect
        self.k["perfectPsi1"] = 0
        self.k["perfectTeta1"] = 0
        self.akkermanRegulator.setCoefficients(self.k, False)
        P = self.akkermanRegulator.regulate(fst)
        P["PL"] -= rot
        P["PR"] += rot
        return P
    def setCoefficients(self, new_coeffs: dict):
        self.k = dict(new_coeffs)
        self.akkermanRegulator.setCoefficients(self.k, True)
