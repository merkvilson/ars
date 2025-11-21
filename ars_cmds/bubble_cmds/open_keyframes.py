import os
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ui.widgets.keyframes import KeyframesWidget
from prefs.pref_controller import get_path
from ars_cmds.util_cmds.copy_to import copy_file_to_dir
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

BBL_KEYFRAMES_CONFIG = {"symbol": ic.ICON_SIZE, "hotkey": "T" }
def BBL_KEYFRAMES(*args):
    run_ext(__file__)

def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
    config.expand = "x"
    config.distribution_mode = "x"
    config.extra_distance = [0,99999]

    options_list = ["1","   ", "A","   ","2"]

    keyframes_widget = KeyframesWidget()
    keyframes_widget.setFixedSize(600, 140)

    config.custom_widget_items = {"A": keyframes_widget,}

    config.image_items = {
    "1": r" ",
    "2": r" ",
    }

    def img_list(keyframe,distance):
        if not os.path.exists(get_path("keyframes")):
            return
        config2 = ContextMenuConfig()
        config2.expand = "y"
        config2.show_symbol = False
        config2.close_on_outside = False
        config2.extra_distance = distance

        items = [os.path.join(get_path("keyframes"),img) for img in os.listdir(get_path("keyframes"))]

        def define_img(img_path):
            ctx.update_item(keyframe, "image_path",  img_path)
            copy_file_to_dir(file_path=img_path, destination_dir=get_path("input"), copy_as=keyframe)


        imgs_dict = {
            img: (lambda img=img: define_img(img_path=img))
            for img in items
        }

        config2.image_items = {
            img: img
            for img in items
        }


        config2.callbackL = imgs_dict

        ctx2=open_context(
            items=items,
            config=config2
        )

    config.callbackL = {
        "1": lambda: img_list("1", [-9999,0]),
        "2": lambda: img_list("2", [9999,0]),
        }

    ctx = open_context(
        items=options_list,
        config=config
    )


