from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import os

def BBL_TEST3(*args):
    run_ext(__file__)


def execute_plugin(self):
    config = ContextMenuConfig()
    
    config.options = {
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
                        "1": lambda: self.render_manager.set_workflow("mesh"),
                        "2": lambda: self.render_manager.set_workflow("render"),
                        "3": lambda: self.render_manager.set_workflow("mesh_image"),
                        "4": lambda: self.render_manager.set_workflow("sprite"),
                        "5": lambda: self.render_manager.set_workflow("video"),
                        "6": lambda: self.render_manager.send_render(),
                        }

    config.callback_hover_in = {"0": lambda: self.msg("render_workflow")}
    config.callback_hover_out = {"0": lambda: self.msg("render_manager")}

    ctx = open_context(config)
