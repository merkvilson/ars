from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from prefs.pref_controller import edit_pref, read_pref
from ars_cmds.core_cmds.run_ext import run_ext

import os
import subprocess
import socket
import pyperclip



def get_local_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip


def start_comfy(server = False, cpu = False):
    cui_root = read_pref("cui_root")
    cui_python = os.path.join(cui_root, "python_embeded", "python.exe")
    cmd = f'"{cui_python}" -s "{os.path.join(cui_root, "ComfyUI", "main.py")}" {"--cpu" if cpu else ""} --windows-standalone-build {"--listen 0.0.0.0 --port 8188" if server else ""}'
    subprocess.Popen(cmd, shell=True)  # Use Popen instead of run to avoid blocking
    if server:
        print(f"ComfyUI server started at http://{get_local_ip()}:8188")
        pyperclip.copy(f"http://{get_local_ip()}:8188")
        
    

def open_comfy():
    config = CtxConfig()
    config.auto_close = False
    config.close_on_outside = False

    options_list = [ "a", ("b",), ("c",)]
    config.additional_texts = {
        "a": "ComfyUI",
        "b": "Server",
        "c": "CPU"
    }

    config.callbackL = { "a": lambda: start_comfy(server=ctx.get_value("b"), cpu=ctx.get_value("c"))}

    ctx = config.open_context(items=options_list)


BBL_X_CONFIG ={"symbol": ic.ICON_SETTINGS }
def BBL_X(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = CtxConfig()

    config.options = {
    "1": "ComfyUI Path",
    ic.ICON_CODE: "Dev Mode",
    "3": "Option 3",
    "4": "ComfyUI Server",
    }
    config.toggle_values = { ic.ICON_CODE: (0,1,ars_window.prefs.dev_mode) }

    config.callbackL = {
    "1": edit_pref,
    ic.ICON_CODE: lambda value: setattr(ars_window.prefs, 'dev_mode', value),
    
    "4": open_comfy,}

    ctx = config.open_context()
