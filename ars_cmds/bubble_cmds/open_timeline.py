import os
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ui.widgets.timeline import TimelineWidget
from prefs.pref_controller import get_path

BBL_TIMELINE_CONFIG = {"symbol": ic.ICON_SIZE, "hotkey": "T" }
def BBL_TIMELINE(self, position):
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
    config.expand = "x"
    config.distribution_mode = "x"
    config.extra_distance = [0,99999]

    options_list = ["1","   ", "A","   ","2"]

    timeline_widget = TimelineWidget()
    timeline_widget.setFixedSize(600, 140)

    config.custom_widget_items = {"A": timeline_widget,}

    config.image_items = {
    "1": r" ",
    "2": r" ",
    }

    def img_list(keyframe,distance):
        config2 = ContextMenuConfig()
        config2.expand = "y"
        config2.show_symbol = False
        config2.close_on_outside = False
        config2.extra_distance = distance

        items = [os.path.join(get_path("keyframes"),img) for img in os.listdir(get_path("keyframes"))]

        imgs_dict = {
            img: (lambda img=img: ctx.update_item(keyframe, "image_path",  img))
            for img in items
        }

        config2.image_items = {
            img: img
            for img in items
        }


        config2.callbackL = imgs_dict

        ctx2=open_context(
            parent=self.central_widget,
            items=items,
            position=position,
            config=config2
        )

    config.callbackL = {
        "1": lambda: img_list("1", [-9999,0]),
        "2": lambda: img_list("2", [9999,0]),
        }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )


