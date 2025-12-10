from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object as get_selected
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from ars_cmds.core_cmds.load_object import add_primitive
from ars_cmds.core_cmds.key_check import key_check_continuous
from core.cursor_modifier import get_cursor, set_cursor
import time

BBL_CAMVIEWER_CONFIG = {"symbol": ic.ICON_WINDOW_MINIMIZE, "hotkey": "V"}


def BBL_CAMVIEWER(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    if getattr(ars_window, "ctx_key_active", False):return
    if time.time() - getattr(ars_window, "ctx_key_last_end", 0) < 0.2:return
    ars_window.ctx_key_active = True

    config = ContextMenuConfig()
    config.options = {
        ic.ICON_HOME: "Home",
        ic.ICON_WINDOW_FULLSCREEN: "Selected",
        ic.ICON_CIRCLE_DASHED: "Cursor"
    }

    camera = ars_window.viewport.cam
    default_rotation = (camera._reset_rotation1, camera._reset_rotation2)

    def view_cursor():
        new_xyz = get_xyz(ars_window)
        
        camera.move_to(center=new_xyz, offset=10 if new_xyz else -10, animate=True)


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
        ic.ICON_CIRCLE_DASHED: view_cursor,
    }

    config.hotkey_items = {
        ic.ICON_HOME: "H",
        ic.ICON_WINDOW_FULLSCREEN: "S",
        ic.ICON_CIRCLE_DASHED: "C",
        
    }

    start_time = 0

    def start():
        nonlocal start_time
        start_time = time.time()
        ars_window.hotkey_manager._unbind_all()
    

    def during():
        if get_cursor()[0] == "map-pin":
           return
        if time.time() - start_time > 0.15:
            set_cursor("map-pin", "bottom")

    
    def end():
        ars_window.ctx_key_active = False
        ars_window.ctx_key_last_end = time.time()
        set_cursor("cursor")
        try:
            if time.time() - start_time > 0.15:
                view_cursor()
            else:
                open_context(config)
        finally:
            ars_window.hotkey_manager._bind_shortcuts()



    key_check_continuous(callback=during,
                         key="V",
                         interval=16,
                         callback_start=start,
                         callback_end=end
                         )
