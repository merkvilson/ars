from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ui.widgets.hierarchy_tree import ObjectHierarchyWindow


BBL_LIST_CONFIG ={"symbol": ic.ICON_LIST }
def BBL_LIST(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = CtxConfig()
    config.dock_area = "left"
    config.auto_close = False
    config.close_on_outside = False

    # Create Object Hierarchy Widget    
    hierarchy = ObjectHierarchyWindow(ars_window.viewport)

    config.custom_widget_items = {"hierarchy": hierarchy}
    options_list =["hierarchy"]
    
    ctx = config.open_context(items=options_list, parent=ars_window.central_widget)

