from enum import Enum
from math import pi
from natsort import natsorted
import interface
import time
import json
import os


class Constants(Enum):
    RAIZ_2 = 1.41421356237
    PI = pi


class Conversions(Enum):
    Vrms = (Constants.RAIZ_2.value, True)
    Vpp = (0.5, True)
    uF = (1e-6, False)
    mA = (1e-3, False)


class ExecMode(Enum):
    FULL = "Totalmente automático"
    SEMI = "Semi-automático"


class Logger:

    __instance = None

    class LoggerHandler:
        def __init__(self):
            self.arq = open("log.txt", "a")

        def __del__(self):
            self.arq.close()

        def write_log(self, text):
            self.arq.write(text)

    class LogType(Enum):
        INFO = "[INFO] "
        ERROR = "[ERRO] "

    @classmethod
    def log(cls, text: str, type: LogType = LogType.INFO):
        if Logger.__instance is None:
            Logger.__instance = Logger.LoggerHandler()

        t = time.localtime()
        current_time = time.strftime("%d/%m/%Y %H:%M:%S ", t)
        Logger.__instance.write_log(f"[{current_time}]{type.value}{text}")


def save_config(config):
    with open("config.json", "w") as arq:
        json.dump(config, arq)


def get_sorted_folder(path):
    return natsorted(os.listdir(path))


if __name__ == "__main__":
    # Load config file
    with open("config.json", "r") as arq:
        config = json.load(arq)

    # Initialize GUI
    interface.GraphicInterface(config)
