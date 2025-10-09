from   ui.widgets.bubble_layout import BubbleConfig
import ars_cmds.bubble_cmds as Bcmd
from   PyQt6.QtCore import QPoint
from   theme.fonts.font_icons import *
import os
import importlib
import inspect

def bubble_pos(bubble):
    res = bubble.pos() + QPoint(bubble.width() // 2, bubble.height() // 2)
    return res

def distribute_bubbles(self):

    for filename in os.listdir(os.path.join('ars_cmds','bubble_cmds')):
        if filename.endswith(".py") and "__init__" not in filename:
            module_name = filename[:-3]
            module = importlib.import_module(f"ars_cmds.bubble_cmds.{module_name}")
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("BBL_"):
                    stem = name[4:]
                    config_var = name + "_CONFIG"
                    if hasattr(module, config_var):
                        config_dict = getattr(module, config_var)
                        if isinstance(config_dict, dict):
                            symbol = config_dict.get("symbol", stem)
                        else:
                            symbol = stem
                    else:
                        symbol = globals().get(f'ICON_{stem.upper()}', stem)
                    config = BubbleConfig()
                    config.symbol = symbol
                    bubble = self.bubbles_overlay.add_bubble(config)
                    bubble.config.callbackL = lambda bb=bubble, f=func: f(self, bubble_pos(bb))
                    bubble.config.callbackR = lambda bb=bubble: Bcmd.r_dropdown(self, bubble_pos(bb))