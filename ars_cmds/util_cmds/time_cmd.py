from PyQt6.QtCore import QTimer

def after(ms, cmd):
    QTimer.singleShot(ms, cmd)