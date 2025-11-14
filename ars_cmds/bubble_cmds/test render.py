from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import os
from PyQt6.QtGui import QCursor, QColor
import random
from PyQt6.QtCore import QPoint

def BBL_TEST3(self, position):
    run_ext(__file__, self)


def execute_plugin(self):
    config = ContextMenuConfig()
    options_list = [
        ["0","1", "2", "3", "4", "5", "6"],
    ]
    
    config.slider_values = {ic.ICON_GIZMO_MOVE: (0,1,0)}
    config.slider_color = {ic.ICON_GIZMO_MOVE: QColor(150, 150, 150, 0)}
    config.use_extended_shape_items = {ic.ICON_GIZMO_MOVE: False}

    config.additional_texts = {
    "0": "Current Workflow",
    "1": "Mesh Workflow",
    "2": "Render Workflow",
    "3": "Mesh Img Workflow",
    "4": "Sprite Workflow",
    "5": "Video Workflow",
    "6": "Start Render",
    }



    config.callbackL = {
                        "0": lambda: print(self.render_manager.workflow_name),
                        "1": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "mesh.json")),
                        "2": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "render.json")),
                        "3": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "mesh_image.json")),
                        "4": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "sprite.json")),
                        "5": lambda: self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "video.json")),
                        "6": lambda: self.render_manager.send_render(),
                        }

    config.callback_hover_in = {"0": lambda: self.ttip("render_workflow")}
    config.callback_hover_out = {"0": lambda: self.ttip("render_manager")}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )
