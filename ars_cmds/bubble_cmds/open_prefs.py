from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *
from prefs.pref_controller import edit_pref, read_pref
import json



BBL_X_CONFIG ={"symbol": ICON_SETTINGS }
def BBL_X(self, position):
    config = ContextMenuConfig()


    options_list = [
        ["1", "2", "3"],
    ]

    config.callbackL = {
    "1": edit_pref,
    "2": read_pref,
    }

    config.additional_texts = {
    "1": "ComfyUI Path",
    "2": "Option 2",
    "3": "Option 3",
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
