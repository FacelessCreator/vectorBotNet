import numpy as np
import defaults

def coefficients(tp, const:dict):
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
    K = np.array([[0, 0, 1]]).dot( np.linalg.inv(Y)).dot( f ) 
    #print(K)

    return K

if __name__ == "__main__":
    consts = defaults.getCoeffs()
    K = coefficients(0.5, consts)
    print(K)