"""
Airen Studio (ARS) - Alpha Version - 0.51

Airen Studio is an AI-powered 3D aimed media software designed to integrate
advanced 3D rendering with AI workflows. This application features a unique
"Floating Bubble" interface, ComfyUI integration, and a modular command system.

Airen Studio - Standalone application
Airen 4D - Plugin for Cinema 4D
Airen Comfy - ComfyUI Extension

Main Application Entry Point.
"""

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["QT_QPA_PLATFORM"] = "windows:fontengine=freetype"
os.environ['QT_LOGGING_RULES'] = 'qt.multimedia*=false'
#Todo: Check if it is possible to add dict into os.environ for more complex settings

# Suppress FFmpeg stderr output at file descriptor level before any Qt imports
import sys
if os.environ.get("ARS_SHOW_STDERR") != "1":
    _devnull = os.open(os.devnull, os.O_WRONLY)
    _old_stderr = os.dup(2)
    os.dup2(_devnull, 2)
    os.close(_devnull)


import pygame
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)  # Standard settings for short sounds

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow


class Application:

    def __init__(self):
        self._app = None
        self._main_window = None

    def run(self) -> None:
        self._app = QApplication(sys.argv)
        
        # Ensure Taskbar icon is consistent on Windows by setting AppUserModelID before QApplication
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('airen.studio.ars')
        icon_path = os.path.join("res", "icon.png")
        if os.path.exists(icon_path):
            self._app.setWindowIcon(QIcon(icon_path))

        self._main_window = MainWindow()
        self._main_window.resize(1920, 1080)
        self._main_window.show()
        #self._main_window.showMaximized()
        #self._main_window.showFullScreen()
        sys.exit(self._app.exec())

def main() -> None:
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
