"""
Airen Studio (ARS) - Alpha Version - 0.50

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

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import ctypes

import pygame
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)  # Standard settings for short sounds

class Application:

    def __init__(self):
        self._app = None
        self._main_window = None

    def run(self) -> None:
        self._app = QApplication(sys.argv)
        self._main_window = MainWindow()
        self._main_window.resize(1280, 720)
        self._main_window.show()
        #self._main_window.showMaximized()
        #self._main_window.showFullScreen()
        sys.exit(self._app.exec())

def main() -> None:

    myappid = 'airen.studio.ars.0.50' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = Application()
    app.run()

if __name__ == "__main__":
    main()
