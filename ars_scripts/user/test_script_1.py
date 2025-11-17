from PyQt6.QtCore import QTimer
import random

def delay(f):
    def wrapper(duration = 100):
        QTimer.singleShot(duration, f)
    return wrapper

def doit():
    msg(random.randint(0,100))

delay(lambda: doit())(1000)