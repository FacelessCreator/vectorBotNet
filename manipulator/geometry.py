from math import sin, cos, sqrt, atan2, pi, acos, asin
import numpy as np

def anglesToCoords(tetas: list, sizes: list):
    teta1 = tetas[0]
    teta2 = tetas[1]
    teta3 = tetas[2]
    a1 = sizes[0]
    a2 = sizes[1]
    a3 = sizes[2]
    T10 = np.array([[cos(teta1), 0, -sin(teta1), 0], [0, 1, 0, a1], [sin(teta1), 0, cos(teta1), 0], [0, 0, 0, 1]])
    T21 = np.array([[cos(teta2), sin(teta2), 0, a2*sin(teta2)], [-sin(teta2), cos(teta2), 0, a2*cos(teta2)], [0, 0, 1, 0], [0, 0, 0, 1]])
    T32 = np.array([[cos(teta3), sin(teta3), 0, a3*sin(teta3)], [-sin(teta3), cos(teta3), 0, a3*cos(teta3)], [0, 0, 1, 0], [0, 0, 0, 1]])
    k3 = np.array([[0], [0], [0], [1]])
    k0 = T10.dot(T21).dot(T32).dot(k3)
    x = k0[0][0]
    y = k0[1][0]
    z = -k0[2][0]
    return [x, y, z]

def coordsToAngles(coords: list, sizes: list):
    a1 = sizes[0]
    a2 = sizes[1]
    a3 = sizes[2]
    x = coords[0]
    y = coords[1]
    z = coords[2]
    x31 = sqrt(x**2+z**2)
    teta1 = atan2(z, x)
    y31 = y - a1
    teta3 = pi - acos((a2**2+a3**2-x31**2-y31**2)/(2*a2*a3))
    teta2 = pi/2 - acos((a2**2+y31**2+x31**2-a3**2)/(2*a2*sqrt(x31**2+y31**2))) - atan2(y31, x31)
    return [teta1, teta2, teta3]

if __name__ == "__main__":
    sizes = [1, 1, 1]
    tetas = [0, -pi/2, -pi/2]
    coords = anglesToCoords(tetas, sizes)
    print(coords)
    tetas = coordsToAngles(coords, sizes)
    print(tetas)