from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext


# BBL_top_row_CONFIG ={"symbol": ic.ICON_, "visible": False }
def BBL_L(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = CtxConfig()
    config.dock_area = "top"
    config.auto_close = False
    config.close_on_outside = False
    config.background_color = (0, 0, 0, 5)
    config.use_extended_shape = False
    config.item_radius = 5 


    config.options = {"": ""}
    
    ctx = config.open_context(parent=ars_window.central_widget)

