from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import os
from PyQt6.QtGui import QCursor, QColor
import random
from PyQt6.QtCore import QPoint

def BBL_2(self, position):
    run_ext(__file__, self)

def doit(self):
    config = ContextMenuConfig()
    options_list = [
        ["1", "2", "3", "4", ic.ICON_GIZMO_MOVE],
    ]
    
    config.auto_close = False
    config.close_on_outside = False

    config.slider_values = {ic.ICON_GIZMO_MOVE: (0,1,0)}
    config.slider_color = {ic.ICON_GIZMO_MOVE: QColor(150, 150, 150, 0)}
    config.use_extended_shape_items = {ic.ICON_GIZMO_MOVE: False}

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
                        ic.ICON_GIZMO_MOVE: lambda value: ctx.move(  self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )

                        }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    doit(window)
