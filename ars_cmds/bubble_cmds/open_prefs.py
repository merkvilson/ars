from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from prefs.pref_controller import edit_pref, read_pref
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor



BBL_X_CONFIG ={"symbol": ic.ICON_SETTINGS }
def BBL_X(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
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
        parent=ars_window.central_widget,
        items=options_list,
        position=ars_window.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )
