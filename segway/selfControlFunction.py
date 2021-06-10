import sys
sys.path.insert(1, 'build 3/segway')

from Xlogging import Logging
from physics import Physics
from regulator import Regulator
import math
import defaults

def selfControlFunction(physics: Physics, logging: Logging, regulator: Regulator, coeffs: dict, target: dict):
    nst = new_state_vector = physics.getStatus()
    fst = full_state_vector = logging.last()

    dt = fst["dt"] = nst["t"] - fst["t"] #ибо используем много, а каждый раз прописывать лень

    fst["tetaL1"] = (nst["tetaL"] - fst["tetaL"]) / dt
    fst["tetaR1"] = (nst["tetaR"] - fst["tetaR"]) / dt
    new_teta = (nst["tetaL"] + nst["tetaR"]) /2
    fst["teta1"] = (new_teta - fst["teta"]) / dt
    fst["teta"] = new_teta
    
    dxl = fst["teta1"] * coeffs["r"]
    fst["xl"] += dxl
    fst["xl1"] = dxl / dt

    beta1 = coeffs["r"]/coeffs["B"] * (fst["tetaR1"] - fst["tetaL1"])
    fst["beta"] += beta1 * dt
    x1 = math.cos(fst["beta"]) * fst["xl1"]
    y1 = math.sin(fst["beta"]) * fst["xl1"]
    fst["x"] += x1 * dt
    fst["y"] += y1 * dt

    ex = target["xT"]-fst["x"]
    ey = target["yT"]-fst["y"]

    fst["gamma"] = math.atan2(ey, ex)
    fst["alpha"] = fst["gamma"] - fst["beta"] # угол ошибки
    if (abs(fst["alpha"]) > math.pi): # не забываем про выход за границы множества углов [-pi; pi)
        fst["alpha"] = fst["alpha"] - math.copysign(1, fst["alpha"]) * 2 * math.pi
    
    fst["ro"] = math.sqrt(ey**2 + ex**2)
    fst["tetaT"] = fst["teta"] + fst["ro"] * math.cos(fst["alpha"]) / coeffs["r"]

    #обновляем все остальные базовые характеристики
    full_state_vector.update(new_state_vector)

    logging.add(full_state_vector)
    power_vector = regulator.regulate(full_state_vector)
    physics.setRegulation(power_vector)

