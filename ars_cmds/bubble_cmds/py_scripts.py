from ui.widgets.context_menu import ContextMenuConfig, open_context
from ui.widgets.ars_code import CodeEditor
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.util_cmds.open_file import open_file
import os
from ars_cmds.core_cmds.load_object import selected_object, add_primitive
from ars_cmds.util_cmds.time_cmd import after

def BBL_CODE_TERMINAL(*args):
    run_ext(__file__)



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
    config.extra_distance = [0,-20]


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
        items= [str(i) for i in range(len(py_files))],
        config=config
    )



def execute_plugin(ars_window):
    py_files = _list_user_scripts()
    if not py_files:
        print("No python scripts found in ars_scripts/user")
        return
    config = ContextMenuConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside=False
    # config.expand = "x"
    config.distribution_mode = "x"
    config.custom_height = int(ars_window.height() / 1.125)
    config.custom_width = ars_window.width() 
    config.extra_distance = [0, 99999]

    current_code_file = os.path.join(user_script_dir, py_files[0])
    with open(current_code_file, 'r', encoding='utf-8') as f:
        current_code_text = f.read()

    options_list = [["   ",ic.ICON_LIST,ic.ICON_FOLDER_OPEN, ic.ICON_PLAYER_PLAY, ic.ICON_SAVE, ic.ICON_CODE_TERMINAL,"   ",], ["   ","PythonEditorWidget","   ",]]
    code_editor = CodeEditor()
    code_editor.setFixedSize(int(ars_window.width() - 10), int(config.custom_height-int(44*1.5)))
    code_editor.setPlainText(current_code_text)

    config.additional_texts = {ic.ICON_LIST: "Scripts List",ic.ICON_FOLDER_OPEN: "Scripts Folder", ic.ICON_PLAYER_PLAY: "Run", ic.ICON_SAVE: "Save", ic.ICON_CODE_TERMINAL: "Open IDE" }
    
    config.custom_widget_items = {"PythonEditorWidget": code_editor}


    def read_code_file(new_file):
        nonlocal current_code_file
        current_code_file = new_file
        with open(new_file, 'r', encoding='utf-8') as f:
            new_file = f.read()
        code_editor.setPlainText(new_file)



    default_namespace_injection = {'ars_window': ars_window,
                                'get_selected': selected_object,
                                'msg': ars_window.msg,
                                'add_primitive': add_primitive,
                                'after': after,}
    
    code_editor.custom_namespace = default_namespace_injection
    code_editor.project_file_path = current_code_file


    config.callbackL = {
        ic.ICON_LIST:           lambda: scripts_ctx(ars_window, read_code_file),
        ic.ICON_FOLDER_OPEN:    lambda: open_file(os.path.join("ars_scripts", "user")),

        ic.ICON_PLAYER_PLAY:    lambda: code_editor.run_code(default_namespace_injection),
        ic.ICON_SAVE:           lambda: code_editor.save_script(),
        ic.ICON_CODE_TERMINAL:  lambda: open_file(code_editor.project_file_path)
                        }

    ctx = open_context(
        items=options_list,
        config=config
    )
    return ctx, code_editor