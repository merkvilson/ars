from theme.fonts.font_icons import *


def clamp(n, min_value, max_value):
    return max(min_value, min(n, max_value))

def cam_speed_up(self):
    current_value = self.viewport._view.camera.scale_factor
    new_value = current_value * 1.1
    new_value = clamp(new_value, 1, 180)
    self.viewport._view.camera.scale_factor = new_value
    result = "Speed: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ICON_SPEED_UP)

def cam_speed_down(self):  
    current_value = self.viewport._view.camera.scale_factor
    new_value = current_value * 0.9
    new_value = clamp(new_value, 1, 180)
    self.viewport._view.camera.scale_factor = new_value
    result = "Speed: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ICON_SPEED_DOWN)

def cam_fow_add(self):  
    current_value = self.viewport._view.camera.fov
    new_value = current_value +5
    new_value = clamp(new_value, 1, 180)
    self.viewport._view.camera.fov = new_value
    result = "View: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ICON_EYE_PLUS)        

def cam_fow_sub(self):  
    current_value = self.viewport._view.camera.fov
    new_value = current_value - 5
    new_value = clamp(new_value, 1, 180)
    self.viewport._view.camera.fov = new_value
    result = "View: " + str(round(new_value, 0))
    self.CF.UP("additional_text", result, ICON_EYE_MINUS)