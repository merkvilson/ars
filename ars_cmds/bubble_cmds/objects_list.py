from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ui.widgets.hierarchy_tree import ObjectHierarchyWindow
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtCore import Qt


BBL_LIST_CONFIG ={"symbol": ic.ICON_LIST }
def BBL_LIST(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = CtxConfig()
    config.dock_area = "left"
    config.distribution_mode = "y"
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = False
    
    # Set width from prefs or default
    config.custom_width = getattr(ars_window.prefs, 'objects_list_width', 300)
    
    hierarchy = ObjectHierarchyWindow(ars_window.viewport)

    config.custom_widget_items = {
        "Hierarchy": hierarchy
    }
    
    options_list =["Hierarchy"]
    
    
    
    ctx = config.open_context(items=options_list, parent=ars_window.central_widget)

