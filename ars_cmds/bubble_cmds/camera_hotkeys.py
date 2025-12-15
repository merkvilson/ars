
from theme.fonts import font_icons as ic
from util_functions.ars_window import ars_window

def clamp(n, min_value, max_value):
    return max(min_value, min(n, max_value))

def cam_move_in(self):
    self.viewport.cam.move_to(offset=-10, animate=True)

def cam_move_out(self):
    self.viewport.cam.move_to(offset=10, animate=True)

def cam_speed_up(self):
    current_value = self.viewport.cam.scale_factor
    new_value = current_value * 1.1
    new_value = clamp(new_value, 1, 180)
    self.viewport.cam.scale_factor = new_value
    result = "Speed: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ic.ICON_SPEED_UP)

def cam_speed_down(self):  
    current_value = self.viewport.cam.scale_factor
    new_value = current_value * 0.9
    new_value = clamp(new_value, 1, 180)
    self.viewport.cam.scale_factor = new_value
    result = "Speed: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ic.ICON_SPEED_DOWN)

def cam_fow_add(self):  
    current_value = self.viewport.cam.fov
    new_value = current_value +5
    new_value = clamp(new_value, 1, 180)
    self.viewport.cam.fov = new_value
    result = "View: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ic.ICON_EYE_PLUS)        

def cam_fow_sub(self):  
    current_value = self.viewport.cam.fov
    new_value = current_value - 5
    new_value = clamp(new_value, 1, 180)
    self.viewport.cam.fov = new_value
    result = "View: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ic.ICON_EYE_MINUS)

# Camera FOV Commands
BBL_cam_fow_add_CONFIG = {"symbol": ic.ICON_EYE_PLUS, "hotkey": "Shift+mouse-wheel-down", "hidden": True}
def BBL_cam_fow_add(*args):
    cam_fow_add(ars_window())

BBL_cam_fow_sub_CONFIG = {"symbol": ic.ICON_EYE_MINUS, "hotkey": "Shift+mouse-wheel-up", "hidden": True}
def BBL_cam_fow_sub(*args):
    cam_fow_sub(ars_window())

# Camera Speed Commands
BBL_cam_speed_up_CONFIG = {"symbol": ic.ICON_SPEED_UP, "hotkey": "Ctrl+mouse-wheel-up", "hidden": True}
def BBL_cam_speed_up(*args):
    cam_speed_up(ars_window())

BBL_cam_speed_down_CONFIG = {"symbol": ic.ICON_SPEED_DOWN, "hotkey": "Ctrl+mouse-wheel-down", "hidden": True}
def BBL_cam_speed_down(*args):
    cam_speed_down(ars_window())

# Camera Move Commands
BBL_cam_move_in_CONFIG = {"symbol": ic.ICON_ZOOM_IN, "hotkey": "Alt+mouse-wheel-up", "hidden": True}
def BBL_cam_move_in(*args):
    cam_move_in(ars_window())

BBL_cam_move_out_CONFIG = {"symbol": ic.ICON_ZOOM_OUT, "hotkey": "Alt+mouse-wheel-down", "hidden": True}
def BBL_cam_move_out(*args):
    cam_move_out(ars_window())


BBL_tst_CONFIG = {"symbol": None, "hotkey": "#", "hidden": True}
def BBL_tst(*args):
    print("Test")
