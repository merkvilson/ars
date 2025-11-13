from ui.widgets.context_menu import ContextMenuConfig, open_context
from ui.widgets.py_code_editor import PythonEditorWidget
from theme.fonts import font_icons as ic
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.run_ext import run_ext, run_raw_script

import os
import subprocess
import platform


BBL_TEST_CONFIG = {"symbol": ic.ICON_CODE_PYTHON}
def BBL_CODE_PYTHON(self, position):
    run_ext(__file__, self)



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
py_files = [f for f in os.listdir(user_script_dir) if f.endswith('.py')]

# Create options list as string numbers
options_list = [str(i) for i in range(len(py_files))]

def scripts_ctx(self, callback_ctx):
    config = ContextMenuConfig()
    config.auto_close = True
    config.close_on_outside=False
    config.show_symbol = False
    config.anchor = "+y"


    # Dynamically create dictionaries for all Python files
    config.additional_texts = {}
    config.callbackL = {}
    config.callbackR = {}

    for i, filename in enumerate(py_files):
        index_str = str(i)
        full_path = os.path.join(user_script_dir, filename)
        config.additional_texts[index_str] = filename  # Key matches the item (string number)
        config.callbackL[index_str] = lambda f=full_path: callback_ctx(f)#run_raw_script(f, self)
        config.callbackR[index_str] = lambda f=full_path: open_file(f)



    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )


def main(self, position):
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside=False
    config.expand = "x"
    config.distribution_mode = "y"
    config.extra_distance = [0,99999]

    current_code_file = os.path.join(user_script_dir, py_files[0])
    with open(current_code_file, 'r', encoding='utf-8') as f:
        current_code_text = f.read()

    options_list = [["1","2","3"],["PythonEditorWidget"]]
    code_editor = PythonEditorWidget()
    code_editor.setFixedSize(self.width() - 44*5, 140)
    code_editor.editor.setPlainText(current_code_text)

    config.additional_texts = {"1": "Scripts List", "2": "Scripts Folder", "3": "Execute"}
    
    config.custom_widget_items = {"PythonEditorWidget": code_editor}

    def save_and_run():
        # Save current code to the file
        with open(current_code_file, 'w', encoding='utf-8') as f:
            f.write(code_editor.editor.toPlainText())
        # Run the saved script
        run_raw_script(current_code_file, self)
    
    def update_current_code_file(new_file):
        nonlocal current_code_file
        current_code_file = new_file
        with open(current_code_file, 'r', encoding='utf-8') as f:
            current_code_text = f.read()
        code_editor.editor.setPlainText(current_code_text)

    config.callbackL = {"1": lambda: scripts_ctx(self, update_current_code_file),
                        "2": lambda: open_file(os.path.join("ars_scripts", "user")),
                        "3": lambda: save_and_run()
                        }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )

def execute_plugin(window):
    main(window, position=window.central_widget.mapFromGlobal(QCursor.pos()))
