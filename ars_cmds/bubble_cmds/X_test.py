#TODO: Fix hotkey toggle

from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *
from PyQt6.QtGui import  QColor
from core.cursor_modifier import show_cursor
from ..render_cmds.render_pass import save_depth
def BBL_OBJ_BOX(self, position):
    config = ContextMenuConfig()
    config.auto_close = False
    config.show_value = True

    options_list = [ "1", "2", "A","B","C"]

    config.callbackL = {"A":lambda:show_cursor(False) , "B":lambda:show_cursor(True), "C": lambda: save_depth(self.viewport)}

    config.slider_values = {
    "1":(0,1000,300),
    "2":(0,1000,300),
    }

    config.incremental_values = {
    "1": 10,
    }

    config.slider_color = {"1": QColor(0,0,0,0)}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
