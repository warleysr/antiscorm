from enum import Enum
from math import pi


class Constants(Enum):
    RAIZ_2 = 1.41421356237
    PI = pi


class Conversions(Enum):
    Vrms = Constants.RAIZ_2.value
    uF = 0.000001
    mA = 0.001
