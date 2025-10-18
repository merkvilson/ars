from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import os
from PyQt6.QtGui import QCursor
import random

def BBL_2(self, position):
    run_ext(__file__, self)

def doit(self):
    config = ContextMenuConfig()
    options_list = [
        ["1", "2", "3", "4"],
    ]
    
    self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "mesh_image.json")),


    config.additional_texts = {
    "1": "set userdata",
    "2": "get userdata",
    "3": "workflow template",
    }



    config.callbackL = {"1": lambda: self.render_manager.set_userdata("seed", random.randint(1, 1000)),
                        "2": lambda: print(self.render_manager.workflow_name),
                        }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    doit(window)
