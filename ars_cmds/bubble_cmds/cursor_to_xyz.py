from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor



BBL_CURSOR_XYZ_CONFIG = {"symbol": ic.ICON_OBJ_CIRCLE, "hotkey": "X"}

def BBL_CURSOR_XYZ(*args):
    run_ext(__file__)

def execute_cmd(ars_window):
    #TODO: print cursor coordinates in 3D space/cursor projection on geometry or world grid

    print("Cursor 3D coordinates command executed.")