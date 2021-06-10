from manipulator_client import Manipulator
from manipulator_client import *

robot = Manipulator()
robot.set_target([0, 2.5, 0, NaN, NaN, NaN])

print(robot.getVector())
