from ars_cmds import bubble_cmds as Bcmd
from hotkeys.hotkey_manager import HotkeyManager
from hotkeys.hotkey_profile import HotkeyProfile
from theme.fonts.font_icons import *
from PyQt6.QtGui import QCursor, QColor
from ars_cmds.camera_cmds.camera_cmds import *
import os
import importlib
import inspect


def define_hotkeys(self):

    def hk(name, func, key):
        self.hotkey_manager.register_action(name, func)
        default_bindings[name] = key

    default_bindings = {}
    hk("cam_speed_up",   lambda: cam_speed_up(self),   "Shift+mouse-wheel-up")
    hk("cam_speed_down", lambda: cam_speed_down(self), "Shift+mouse-wheel-down")
    hk("cam_fow_add",    lambda: cam_fow_add(self),    "Ctrl+mouse-wheel-down")
    hk("cam_fow_sub",    lambda: cam_fow_sub(self),    "Ctrl+mouse-wheel-up")

    # Dynamically add hotkeys based on BBL functions
    for filename in os.listdir(os.path.join('ars_cmds', 'bubble_cmds')):
        if filename.endswith(".py") and "__init__" not in filename:
            module_name = filename[:-3]
            module = importlib.import_module(f"ars_cmds.bubble_cmds.{module_name}")
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("BBL_"):
                    stem = name[4:]
                    config_var = name + "_CONFIG"
                    if hasattr(module, config_var):
                        config_dict = getattr(module, config_var)
                        if isinstance(config_dict, dict) and "hotkey" in config_dict:
                            hotkey = config_dict["hotkey"]
                            action_name = stem
                            hk(action_name, lambda f=func: f(self, self.central_widget.mapFromGlobal(QCursor.pos())), hotkey)

    default_profile = HotkeyProfile("default", default_bindings)
    self.hotkey_manager.add_profile(default_profile)
    self.hotkey_manager.load_profile("default")