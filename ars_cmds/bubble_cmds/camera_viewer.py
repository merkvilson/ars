from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object as get_selected

BBL_CAMVIEWER_CONFIG = {"symbol": ic.ICON_WINDOW_MINIMIZE, "hotkey": "V"}


def BBL_CAMVIEWER(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = ContextMenuConfig()
    config.options = {
        ic.ICON_HOME: "View Home",
        ic.ICON_WINDOW_FULLSCREEN: "View Selected",
    }

    camera = ars_window.viewport.cam

    def view_selected():
        obj = get_selected()
        if not obj: return
        xyz=obj.get_position()
        camera.move_to(center=tuple(xyz), offset=5, animate=True)
    
    def view_home():
        camera.move_to(center=(0,0,0), offset=10, animate=True)
        
    config.callbackL = {
        ic.ICON_HOME: view_home,
        ic.ICON_WINDOW_FULLSCREEN: view_selected,
    }

    config.hotkey_items = {
        ic.ICON_HOME: "H",
        ic.ICON_WINDOW_FULLSCREEN: "S",
        
    }

    open_context(config)
