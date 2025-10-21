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
    



    config.additional_texts = {
    "1": "Mesh Workflow",
    "2": "Render Workflow",
    "3": "Mesh Img Workflow",
    "4": "Current Workflow",
    }

    def get_obj(self):
        selected = self.viewport._objectManager.get_selected_objects()
        if not selected:
            return
        obj = selected[0]
        return obj
    
    def set_prompt():
        obj = get_obj(self)
        if obj:
            prompt = f"A random number: {random.randint(1,1000)}"
            obj.set_prompt(prompt)
            print(f"Set prompt to: {prompt}")

    config.callbackL = {"1": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "mesh.json")),
                        "2": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "render.json")),
                        "3": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "mesh_image.json")),
                        "4": lambda: print(self.render_manager.workflow_name),

                        }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    doit(window)
