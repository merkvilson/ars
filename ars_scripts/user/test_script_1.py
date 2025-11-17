from PyQt6.QtCore import QTimer

# Delay 2000ms (2 seconds) before showing message
QTimer.singleShot(2000, lambda: msg("Hello Airen!"))
