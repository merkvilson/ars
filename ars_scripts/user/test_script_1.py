from PyQt6.QtCore import QTimer

def f1():
    QTimer.singleShot(100, lambda: msg("Hello Airen!"))
f1()