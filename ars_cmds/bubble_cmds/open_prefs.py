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

    config.options = {
    "1": "ComfyUI Path",
    ic.ICON_CODE: "Dev Mode",
    "3": "Option 3",
    }
    config.toggle_values = { ic.ICON_CODE: (0,1,ars_window.prefs.dev_mode) }

    config.callbackL = {
    "1": edit_pref,
    ic.ICON_CODE: lambda value: setattr(ars_window.prefs, 'dev_mode', value),
    }

    ctx = open_context(config)
