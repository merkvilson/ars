from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ui.widgets.hierarchy_tree import ObjectHierarchyWindow

from ars_cmds.bubble_cmds.delete_selected_obj import BBL_TRASH as delete_cmd
from ars_cmds.bubble_cmds.view_camera import view_selected

BBL_LIST_CONFIG ={"symbol": ic.ICON_LIST }
def BBL_LIST(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = CtxConfig()
    config.expand = "y"
    config.auto_close = False
    config.close_on_outside = False
    config.extra_distance=[9999,0]
    config.use_extended_shape = False
    config.distribution_mode = "x"


    options_list = [
        [ic.ICON_SETTINGS, ic.ICON_TRASH, ic.ICON_FOCUS, ic.ICON_OBJ_BBOX], 
        ["hierarchy"],
        "   ",
        ]
    
    hierarchy = ObjectHierarchyWindow(ars_window.viewport)

    config.custom_widget_items = {"hierarchy": hierarchy}


    config.callbackL = {
        "1": lambda: ctx.close_animated(),

        ic.ICON_TRASH: lambda: delete_cmd(ars_window),
        ic.ICON_FOCUS: lambda: view_selected(),
    }

    ctx = config.open_context(items=options_list)

