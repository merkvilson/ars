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


from PyQt6.QtWidgets import QApplication
from ui.widgets.splash_screen import SplashScreen
from tests.splash_screen_test import show_random_message

class Application:

    def __init__(self):
        self._app = None
        self._main_window = None

    def run(self) -> None:
        # Ensure Taskbar icon is consistent on Windows by setting AppUserModelID before QApplication
        if sys.platform == 'win32':
            import ctypes
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('airen.studio.ars')
            except Exception:
                pass

        self._app = QApplication(sys.argv)
        
        # Show splash screen IMMEDIATELY
        splash = SplashScreen()
        splash.show()
        splash.show_message("Starting Airen Studio...")
        
        # Now do the heavy imports and initialization
        splash.show_message("Loading Audio Engine...")
        import pygame
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        splash.show_message("Loading Core Modules...")

        show_random_message(splash)

        from ui.main_window import MainWindow
        
        self._main_window = MainWindow(splash=splash)
        
        splash.show_message("Preparing Workspace...")
        self._main_window.resize(1920, 1080)
        self._main_window.show()
        
        # Close splash screen after main window is shown
        splash.close()
        
        exit_code = self._app.exec()
        
        # Final cleanup
        try:
            import pygame
            pygame.mixer.quit()
        except ImportError:
            pass
        
        sys.exit(exit_code)

def main() -> None:
    print("Starting Airen Studio...")
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
