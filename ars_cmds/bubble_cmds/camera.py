from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

def clamp(n, min_value, max_value):
    return max(min_value, min(n, max_value))


def cam_speed(ars_window, value):
    ars_window.viewport._view.camera.scale_factor = value

def cam_zoom(ars_window, value):
    ars_window.viewport._view.camera.fov = clamp(value, 1, 175)


BBL_CAMERA_CONFIG = {"symbol": ic.ICON_CAMERA,"hotkey": "C"}
def BBL_CAMERA(*args):
    run_ext(__file__)



def execute_plugin(ars_window):
    config = ContextMenuConfig()
    
    options_list = [ic.ICON_CAMERA, ic.ICON_ORBIT, ic.ICON_FLY, ic.ICON_SPEED_UP, ic.ICON_EYE_UP]


    config.additional_texts = {
        ic.ICON_CAMERA: "Scene Camera",
        ic.ICON_ORBIT:  'Orbit Camera',
        ic.ICON_FLY:    "Fly Camera",
        ic.ICON_SPEED_UP:    "Speed",
        ic.ICON_EYE_UP:    "Field Of View",
    }

    config.hotkey_items = {
        ic.ICON_CAMERA: "S",
        ic.ICON_ORBIT:  'O',
        ic.ICON_FLY:    "F",
    }


    config.slider_values = {
        ic.ICON_SPEED_UP:   (1,100,ars_window.viewport._view.camera.scale_factor),
        ic.ICON_EYE_UP:   (1,180,ars_window.viewport._view.camera.fov),
    }


    config.show_value_items = {
        ic.ICON_SPEED_UP:   True,
        ic.ICON_EYE_UP:   True,
    }

    config.toggle_values = { 
    ic.ICON_CAMERA: (0,1,0),
    ic.ICON_ORBIT: (0,1,0),
    ic.ICON_FLY: (0,1,1),
    }


    config.toggle_groups = [
        [ic.ICON_CAMERA,ic.ICON_ORBIT,ic.ICON_FLY]
    ]
    

    config.show_hotkey = 0

    config.callbackL = {
        ic.ICON_CAMERA: lambda: print("1"),
        ic.ICON_ORBIT:  lambda: print('2'),
        ic.ICON_FLY:    lambda: print("3"),
        ic.ICON_SPEED_UP:    lambda value: cam_speed(ars_window, value),
        ic.ICON_EYE_UP:    lambda value: cam_zoom(ars_window, value),
    }

    ctx = open_context(
        items=options_list,
        config=config
    )
    ctx.symbol = ic.ICON_CAMERA