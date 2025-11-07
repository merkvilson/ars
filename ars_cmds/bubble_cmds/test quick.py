from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.load_object import selected_object
from ui.widgets.multi_line_input import MultiLineInputWidget
from PyQt6.QtCore import QPoint
from prefs.pref_controller import read_pref, get_path
import os
import subprocess
from PyQt6.QtGui import QCursor

def BBL_TEST2(self, position):
    run_ext(__file__, self)

    
def main(self, position):
    config = ContextMenuConfig()
    config.auto_close = False

    options_list = [ "a", ("b",), ("c",), "d"]
    config.additional_texts = {
        "a": "ComfyUI",
        "b": "Server",
        "c": "CPU"
    }

    def start_comfy(server = False, cpu = False):
        cui_root = read_pref("cui_root")
        cui_python = os.path.join(cui_root, "python_embeded", "python.exe")
        cmd = f'"{cui_python}" -s "{os.path.join(cui_root, "ComfyUI", "main.py")}" {"--cpu" if cpu else ""} --windows-standalone-build {"--listen 0.0.0.0 --port 8188" if server else ""}'
        subprocess.run(cmd, shell=True)



    config.callbackL = {
        "a": lambda: start_comfy(server=ctx.get_value("b"), cpu=ctx.get_value("c")),
                        }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )



def execute_plugin(window):
    main(window, QPoint(0, 0))













