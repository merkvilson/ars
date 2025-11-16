from ars_cmds.core_cmds.key_check import key_check_continuous
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object
from PyQt6.QtCore import QPoint, QTimer
from ui.widgets.hierarchy_tree import ObjectHierarchyWindow


BBL_LIST_CONFIG ={"symbol": ic.ICON_LIST }
def BBL_LIST(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.expand = "y"
    config.auto_close = False
    config.close_on_outside = False


    options_list = [
        ["1", "hierarchy"],
    ]
    
    hierarchy = ObjectHierarchyWindow(ars_window.viewport)

    config.custom_widget_items = {"hierarchy": hierarchy}

    config.additional_texts = {
    "1": "Close Hierarchy",
    }


    config.callbackL = {
        "1": lambda: ctx.close_animated(),
    }

    ctx = open_context(
        items=options_list,
        config=config
    )

