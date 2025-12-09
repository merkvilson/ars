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
    default_rotation = (camera._reset_rotation1, camera._reset_rotation2)


    def view_selected():
        obj = get_selected()
        if not obj: return
        xyz=obj.get_position()
        scale_sum = sum(obj.get_scale()) * 2
        camera.move_to(center=tuple(xyz), offset=scale_sum, animate=True, rotation=default_rotation)
    
    def view_home():
        camera.move_to(center=(0,0,0), offset=10, animate=True, rotation=default_rotation)
        
    config.callbackL = {
        ic.ICON_HOME: view_home,
        ic.ICON_WINDOW_FULLSCREEN: view_selected,
    }

    config.hotkey_items = {
        ic.ICON_HOME: "H",
        ic.ICON_WINDOW_FULLSCREEN: "V",
        
    }

    open_context(config)
