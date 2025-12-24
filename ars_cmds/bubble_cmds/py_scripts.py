from ui.widgets.context_menu import CtxConfig
from ui.ars_code import CodeEditorWidget
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.util_cmds.open_file import open_file
import os
from ars_cmds.core_cmds.load_object import selected_object, add_primitive
from ars_cmds.util_cmds.time_cmd import after
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtCore import QTimer
from prefs import pref_controller



def BBL_CODE_TERMINAL(*args):
    run_ext(__file__)



# Filter for .py files only
docs = pref_controller.get_path("documents")
user_script_dir = os.path.join(docs, "scripts")


def _list_user_scripts():
    return sorted(
        f for f in os.listdir(user_script_dir)
        if f.endswith('.py') and os.path.isfile(os.path.join(user_script_dir, f))
    )


def scripts_ctx(ars_window, callback_ctx):
    py_files = _list_user_scripts()
    config = CtxConfig()
    config.auto_close = True
    config.close_on_outside = False
    config.show_symbol = False
    config.anchor = "+y"
    config.extra_distance = [0, -20]

    # Dynamically create dictionaries for all Python files
    config.additional_texts = {}
    config.callbackL = {}
    config.callbackR = {}
    config.text_values = {}
    config.show_symbol_items = {}

    # New File Item
    new_file_key = ic.ICON_TEXT_INPUT
    config.additional_texts[new_file_key] = "New File"
    config.text_value[new_file_key] = ""
    config.show_symbol_items[new_file_key] = True

    def create_new_file(filename):
        if not filename: return
        filename = filename.replace(" ", "_")
        if not filename.endswith(".py"): filename += ".py"
        full_path = os.path.join(user_script_dir, filename)
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                f.write(f"#{filename}\n")
        ars_window.msg(f"Created: {filename}")
        callback_ctx(full_path)
        ctx.close_animated()

    config.callbackL[new_file_key] = create_new_file

    for i, filename in enumerate(py_files):
        index_str = str(i)
        full_path = os.path.join(user_script_dir, filename)
        config.additional_texts[index_str] = filename  # Key matches the item (string number)
        config.callbackL[index_str] = lambda x=None, f=full_path: callback_ctx(f)  # Use lambda to capture current full_path
        config.callbackR[index_str] = lambda x=None, f=full_path: open_file(f)

    items_list = [new_file_key] + [str(i) for i in range(len(py_files))]
    ctx = config.open_context(items=items_list)



def execute_cmd(ars_window, animated=True):
    py_files = _list_user_scripts()

    if not py_files:
        default_script = "script_1.py"
        full_path = os.path.join(user_script_dir, default_script)
        if not os.path.exists(user_script_dir):
            os.makedirs(user_script_dir)
        with open(full_path, 'w') as f:
            f.write("# New script\n")
        py_files = [default_script]

    # if not py_files:
    #     print("No python scripts found in ars_scripts/user")
    #     return
    config = CtxConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = False
    # config.expand = "x"
    config.distribution_mode = "x"
    config.custom_height = ars_window.prefs.code_editor_height
    config.custom_width = ars_window.width()
    config.extra_distance = [0, 99999]

    current_code_file = os.path.join(user_script_dir, py_files[0])
    with open(current_code_file, 'r', encoding='utf-8') as f:
        current_code_text = f.read()

    options_list = [
        [
            ic.ICON_ARROW_BARS_V,
            ic.ICON_TXT_SIZE,
            ic.ICON_SHADER_SMOOTH,
            "   ",
            ic.ICON_LIST,
            ic.ICON_FOLDER_OPEN,
            ic.ICON_PLAYER_PLAY,
            ic.ICON_SAVE,
            ic.ICON_CODE_TERMINAL,
            "   ",
        ],
        ["   ", "SplitterWidget", "   "],
        "   ",
    ]

    available_height = int(config.custom_height - int(44 * 1.5))
    
    # Create CodeEditorWidget (combined editor + terminal)
    code_editor_widget = CodeEditorWidget()
    code_editor_widget.setFixedSize(int(ars_window.width() - 10), available_height)
    code_editor_widget.set_code(current_code_text)
    
    # Get reference to the inner code editor
    code_editor = code_editor_widget.code_editor

    config.custom_widget_items = {
        "SplitterWidget": code_editor_widget
    }
    config.slider_values = {
        ic.ICON_SHADER_SMOOTH: (0, 100, ars_window.prefs.code_editor_alpha*100),
        ic.ICON_ARROW_BARS_V: (int(44 * 1.5), ars_window.height() - int(44 * 1.5) - 20, ars_window.prefs.code_editor_height),
        ic.ICON_TXT_SIZE: (10,48,ars_window.prefs.code_editor_font_size),
    }
    config.incremental_values = {ic.ICON_SHADER_SMOOTH: 3, ic.ICON_ARROW_BARS_V: (-20, "y"),ic.ICON_TXT_SIZE: 1, }
    config.slider_color = {ic.ICON_ARROW_BARS_V: QColor(0, 0, 0, 0)}

    def read_code_file(new_file):
        nonlocal current_code_file
        current_code_file = new_file
        with open(new_file, 'r', encoding='utf-8') as f:
            content = f.read()
        code_editor.setPlainText(content)
        code_editor.project_file_path = current_code_file
        
        def set_focus_delayed():
            code_editor.setFocus()
            cursor = code_editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            code_editor.setTextCursor(cursor)

        QTimer.singleShot(100, set_focus_delayed)

    default_namespace_injection = {
        'ars_window': ars_window,
        'get_selected': selected_object,
        'msg': ars_window.msg,
        'add_primitive': add_primitive,
        'after': after,
        'ic': ic,
    }

    code_editor.custom_namespace = default_namespace_injection
    code_editor.project_file_path = current_code_file
    code_editor_widget.set_font_size(ars_window.prefs.code_editor_font_size)
    code_editor_widget.set_alpha(ars_window.prefs.code_editor_alpha)

    config.callbackL = {
        ic.ICON_LIST: lambda: scripts_ctx(ars_window, read_code_file),
        ic.ICON_FOLDER_OPEN: lambda: open_file(user_script_dir),
        ic.ICON_PLAYER_PLAY: lambda: code_editor_widget.run_code(default_namespace_injection),
        ic.ICON_SAVE: lambda: code_editor_widget.save_script(),
        ic.ICON_CODE_TERMINAL: lambda: open_file(code_editor.project_file_path),
        ic.ICON_TXT_SIZE: lambda value: (
            code_editor_widget.set_font_size(value) ,
            setattr(ars_window.prefs, 'code_editor_font_size', value),
            ),
        ic.ICON_SHADER_SMOOTH: lambda value: (
            ctx.set_alpha(value / 2550.0),
            code_editor_widget.set_alpha(value / 100.0), 
            setattr(ars_window.prefs, 'code_editor_alpha', value / 100.0),
            ),
        ic.ICON_ARROW_BARS_V: lambda value: (
            ctx.resize_top(value),
            code_editor_widget.setFixedHeight(int(value - int(44 * 1.5))),
            setattr(ars_window.prefs, 'code_editor_height', int(value)),
            ),
    }

    ctx = config.open_context(items=options_list, animated=animated)
    return ctx, code_editor_widget
