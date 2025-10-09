from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *


def clamp(n, min_value, max_value):
    return max(min_value, min(n, max_value))


def cam_speed(self, value):
    self.viewport._view.camera.scale_factor = value

def cam_zoom(self, value):
    self.viewport._view.camera.fov = clamp(value, 1, 175)


BBL_CAMERA_CONFIG = {"symbol": ICON_CAMERA,"hotkey": "C"}
def BBL_CAMERA(self, position):
    config = ContextMenuConfig()
    
    options_list = [ICON_CAMERA, ICON_ORBIT, ICON_FLY, ICON_SPEED_UP, ICON_EYE_UP]


    config.additional_texts = {
        ICON_CAMERA: "Scene Camera",
        ICON_ORBIT:  'Orbit Camera',
        ICON_FLY:    "Fly Camera",
        ICON_SPEED_UP:    "Speed",
        ICON_EYE_UP:    "Field Of View",
    }

    config.hotkey_items = {
        ICON_CAMERA: "S",
        ICON_ORBIT:  'O',
        ICON_FLY:    "F",
    }


    config.slider_values = {
        ICON_SPEED_UP:   (1,100,self.viewport._view.camera.scale_factor),
        ICON_EYE_UP:   (1,180,self.viewport._view.camera.fov),
    }


    config.show_value_items = {
        ICON_SPEED_UP:   True,
        ICON_EYE_UP:   True,
    }

    config.toggle_values = { 
    ICON_CAMERA: (0,1,0),
    ICON_ORBIT: (0,1,0),
    ICON_FLY: (0,1,1),
    }


    config.toggle_groups = [
        [ICON_CAMERA,ICON_ORBIT,ICON_FLY]
    ]
    

    config.show_hotkey = 0

    config.callbackL = {
        ICON_CAMERA: lambda: print("1"),
        ICON_ORBIT:  lambda: print('2'),
        ICON_FLY:    lambda: print("3"),
        ICON_SPEED_UP:    lambda value: cam_speed(self, value),
        ICON_EYE_UP:    lambda value: cam_zoom(self, value),
    }

    radial = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )