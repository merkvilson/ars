from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import os

def BBL_TEST3(*args):
    run_ext(__file__)


def execute_plugin(self):
    config = ContextMenuConfig()
    options_list =  ["0","1", "2", "3", "4", "5", "6"]

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

    config.callback_hover_in = {"0": lambda: self.msg("render_workflow")}
    config.callback_hover_out = {"0": lambda: self.msg("render_manager")}

    ctx = open_context(
        items=options_list,
        config=config
    )
