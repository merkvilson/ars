import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_FONT_DPI"] = "200"
os.environ["QT_QPA_PLATFORM"] = "windows:fontengine=freetype"
os.environ['QT_LOGGING_RULES'] = 'qt.multimedia*=false'

import sys
from PyQt6.QtWidgets import QApplication
from core.cursor_modifier import set_default_cursor
from ui.main_window import MainWindow

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
    app = Application()
    app.run()
    set_default_cursor("cursor")

if __name__ == "__main__":
    main()
