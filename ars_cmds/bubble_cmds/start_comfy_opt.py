from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from prefs.pref_controller import read_pref
import os
import subprocess
import socket
import pyperclip

def BBL_C(*args):
    run_ext(__file__)

    

def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.auto_close = False

    options_list = [ "a", ("b",), ("c",)]
    config.additional_texts = {
        "a": "ComfyUI",
        "b": "Server",
        "c": "CPU"
    }

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
            

    config.callbackL = {
        "a": lambda: (start_comfy(server=ctx.get_value("b"), cpu=ctx.get_value("c")),
                      ctx.close_animated()),
                        }

    ctx = open_context(
        items=options_list,
        config=config
    )
    ctx.symbol = "start_comfy_opt"


