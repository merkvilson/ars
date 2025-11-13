from ui.widgets.context_menu import ContextMenuConfig, open_context
from ui.widgets.py_code_editor import PythonEditorWidget
from theme.fonts import font_icons as ic
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.run_ext import run_ext, run_raw_script

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
    run_ext(__file__, self)

def main(self, position):
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside=True
    config.show_symbol = False
    config.expand = "x"
    config.distribution_mode = "x"
    config.extra_distance = [0,99999]

    user_script_dir = os.path.join("ars_scripts", "user")

    # Filter for .py files only
    py_files = [f for f in os.listdir(user_script_dir) if f.endswith('.py')]

    # Create options list as string numbers
    options_list = [str(i) for i in range(len(py_files))]

    # Dynamically create dictionaries for all Python files
    config.additional_texts = {}
    config.callbackL = {}
    config.callbackR = {}

    for i, filename in enumerate(py_files):
        index_str = str(i)
        full_path = os.path.join(user_script_dir, filename)
        config.additional_texts[index_str] = filename  # Key matches the item (string number)
        config.callbackL[index_str] = lambda f=full_path: run_raw_script(f, self)
        config.callbackR[index_str] = lambda f=full_path: open_file(f)

    options_list.append(str(len(py_files)))  #"Open Scripts Folder" option
    config.additional_texts[str(len(py_files))] = "Open Scripts Folder"
    config.callbackL[str(len(py_files))] = lambda: open_file(user_script_dir)

    options_list += ["PythonEditorWidget"]
    code_editor = PythonEditorWidget()
    code_editor.setFixedSize(600, 140)
    
    config.custom_widget_items = {"PythonEditorWidget": code_editor}


    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )



def execute_plugin(window):
    main(window, position=window.central_widget.mapFromGlobal(QCursor.pos()))
