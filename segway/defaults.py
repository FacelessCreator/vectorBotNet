
def getFullStatus():
    full_status = {
        "t": 0,
        "x": 0,
        "y": 0,
        "xl": 0,
        "xl1": 0,
        "psi": 0,
        "psi1": 0,
        "psi11": 0,
        "tetaL": 0,
        "tetaR": 0,
        "tetaL1": 0,
        "tetaR1": 0,
        "teta": 0,
        "teta1": 0,
        "tetaT": 0,
        "ro": 0,
        "alpha": 0,
        "beta": 0,
        "gamma": 0
    }
    return full_status

def getCoeffs():
    coeffs = {
    "r": 0.028, # радиус колеса
    "B": 0.184, # расстояние между центрами колёс
    "mb": 0.282, # масса блока
    "mw": 0.020, # масса колеса
    "l": 0.092, # расстояние между центром колёс и центром блока
    "lbw": 0.072, # ширина со стороны дисплея
    "lbh": 0.110, # высота блока
    "lbt": 0.052, # толщина блока
    "J": 0.0024, # момент инерции ротора
    "km": 0.583,
    "ke": 0.583,
    "R": 8.4,
    "g": 9.81,
    "Umax": 8.3,
    "tp_standart": 6.3, # «стандартное» значение времени переходного процесса
    }
    coeffs["Jb"] = 1/12 * coeffs["mb"] * (coeffs["lbh"]**2 + coeffs["lbt"]**2) + coeffs["mb"]*coeffs["l"]**2 # момент инерции блока относительно цента колёс
    coeffs["Jw"] = 0.5 * coeffs["mw"] * coeffs["r"]**2 # момент инерции колеса
    return coeffs

def getTarget():
    target = {
        "xT": 0,
        "yT": 0
    }
    return target
