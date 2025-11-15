from ui.widgets.context_menu import ContextMenuConfig, open_context
from ui.widgets.py_code_editor import PythonEditorWidget
from theme.fonts import font_icons as ic
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.run_ext import run_ext

import os
import subprocess
import platform


def BBL_CODE_TERMINAL(*args):
    run_ext(__file__)



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


# Filter for .py files only
user_script_dir = os.path.join("ars_scripts", "user")

def _list_user_scripts():
    """Return current list of user python scripts (sorted for stability)."""
    try:
        return sorted(
            f for f in os.listdir(user_script_dir)
            if f.endswith('.py') and os.path.isfile(os.path.join(user_script_dir, f))
        )
    except FileNotFoundError:
        return []



def scripts_ctx(ars_window, callback_ctx):
    py_files = _list_user_scripts()
    config = ContextMenuConfig()
    config.auto_close = True
    config.close_on_outside=False
    config.show_symbol = False
    config.anchor = "+y"
    config.extra_distance = [-99999,-20]



    # Dynamically create dictionaries for all Python files
    config.additional_texts = {}
    config.callbackL = {}
    config.callbackR = {}

    for i, filename in enumerate(py_files):
        index_str = str(i)
        full_path = os.path.join(user_script_dir, filename)
        config.additional_texts[index_str] = filename  # Key matches the item (string number)
        config.callbackL[index_str] = lambda f=full_path: callback_ctx(f)  # Use lambda to capture current full_path
        config.callbackR[index_str] = lambda f=full_path: open_file(f)



    ctx = open_context(
        parent=ars_window.central_widget,
        items= [str(i) for i in range(len(py_files))],
        position=ars_window.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )



def execute_plugin(ars_window):
    py_files = _list_user_scripts()
    if not py_files:
        print("No python scripts found in ars_scripts/user")
        return
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside=False
    config.expand = "x"
    config.distribution_mode = "y"
    config.extra_distance = [0,99999]

    current_code_file = os.path.join(user_script_dir, py_files[0])
    with open(current_code_file, 'r', encoding='utf-8') as f:
        current_code_text = f.read()

    options_list = [[ic.ICON_LIST,ic.ICON_FOLDER_OPEN, ic.ICON_CODE_PYTHON, ic.ICON_SAVE, ic.ICON_CODE_TERMINAL], ["PythonEditorWidget"]]
    code_editor = PythonEditorWidget()
    code_editor.setFixedSize(ars_window.width() - int(44*4.5), 44*5)
    code_editor.editor.setPlainText(current_code_text)

    config.additional_texts = {ic.ICON_LIST: "Scripts List",ic.ICON_FOLDER_OPEN: "Scripts Folder", ic.ICON_CODE_PYTHON: "Run", ic.ICON_SAVE: "Save", ic.ICON_CODE_TERMINAL: "Open IDE" }
    
    config.custom_widget_items = {"PythonEditorWidget": code_editor}


    def read_code_file(new_file):
        nonlocal current_code_file
        current_code_file = new_file
        with open(new_file, 'r', encoding='utf-8') as f:
            new_file = f.read()
        code_editor.editor.setPlainText(new_file)

    
    def save_script():
        with open(current_code_file, 'w', encoding='utf-8') as f:
            f.write(code_editor.editor.toPlainText())



    config.callbackL = {ic.ICON_LIST: lambda: scripts_ctx(ars_window, read_code_file),
                       ic.ICON_FOLDER_OPEN: lambda: open_file(os.path.join("ars_scripts", "user")),
                        ic.ICON_CODE_PYTHON: lambda: code_editor.run_code(),
                        ic.ICON_SAVE: lambda: save_script(),
                        ic.ICON_CODE_TERMINAL: lambda: open_file(current_code_file)
                        }

    ctx = open_context(
        items=options_list,
        config=config
    )