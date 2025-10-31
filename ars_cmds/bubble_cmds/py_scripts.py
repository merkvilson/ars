from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtCore import QPoint


import os
import subprocess
import platform

def open_file(path):
    """Open a file in its default editor/viewer."""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    system = platform.system()

    try:
        if system == "Windows":
            os.startfile(path)  # Windows built-in
        elif system == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Linux or other UNIX-like
            subprocess.run(["xdg-open", path])
        print(f"Opened: {path}")
    except Exception as e:
        print(f"Failed to open file: {e}")




BBL_TEST_CONFIG = {"symbol": ic.ICON_CODE_PYTHON}
def BBL_CODE_PYTHON(self, position):

    config = ContextMenuConfig()
    config.auto_close = False

    options_list = [ "1","2","3"]
    config.additional_texts = {
        "1": "Run Script",
        "2": "Open Script",
        "3": "Close",
    }
    file_path = r"C:\Users\gmerk\Downloads\ARS\ars_cmds\bubble_cmds\test_script.py"

    config.callbackL = {
                        "1": lambda: run_ext(file_path, self),
                        "2": lambda: open_file(file_path),
                        "3": lambda: ctx.close_animated(),
                        }

    

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )



