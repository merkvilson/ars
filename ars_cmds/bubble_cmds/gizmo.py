"""
This module provides gizmo control functionality (move, rotate, scale) via a context menu.
"""
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.key_check import key_check_continuous
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from core.cursor_modifier import get_cursor, set_cursor
import time

BBL_GIZMO_MOVE_CONFIG = {"symbol": ic.ICON_GIZMO_MOVE, "hotkey": "Q"}


def BBL_GIZMO_MOVE(*args):
    """
    Entry point for the gizmo bubble command.
    Runs the current file as an extension.
    """
    run_ext(__file__)


def execute_cmd(ars_window):
    """
    Executes the gizmo plugin.
    
    Opens a context menu allowing the user to switch between different gizmo modes
    (Move, Rotate, Scale, Drag) for the currently selected object.
    
    Args:
        ars_window: The main application window instance.
    """
    obj = selected_object()
    if not obj:
        return

    if getattr(ars_window, "ctx_key_active", False):return
    if time.time() - getattr(ars_window, "ctx_key_last_end", 0) < 0.2:return
    ars_window.ctx_key_active = True

    

    config = ContextMenuConfig()

    config.options = {
        ic.ICON_GIZMO_MOVE_3D: "Move",
        ic.ICON_GIZMO_ROTATE_3D: "Rotate",
        ic.ICON_GIZMO_SCALE: "Scale",
        ic.ICON_GIZMO_DRAG: "Quick Drag",
    }


    config.toggle_values = {
        ic.ICON_GIZMO_MOVE_3D: (0, 1, ars_window.viewport.controller.get_visibility("move")),
        ic.ICON_GIZMO_SCALE: (0, 1, ars_window.viewport.controller.get_visibility("scale")),
        ic.ICON_GIZMO_ROTATE_3D: (0, 1, ars_window.viewport.controller.get_visibility("rotate")),
        #ic.ICON_GIZMO_DRAG: (0, 1, 0), #TODO: Implement drag gizmo toggle
    }

    config.toggle_groups = [
        [ic.ICON_GIZMO_MOVE_3D, ic.ICON_GIZMO_ROTATE_3D, ic.ICON_GIZMO_SCALE],
    ]

    config.hotkey_items = {
        ic.ICON_GIZMO_MOVE_3D: "W",
        ic.ICON_GIZMO_SCALE: "E",
        ic.ICON_GIZMO_ROTATE_3D: "R",
        ic.ICON_GIZMO_DRAG: "Q",
    }

    def move_obj(time=0.25):
            new_xyz = get_xyz(ars_window, ignore_objs=[obj])
            if new_xyz:
                obj.move_to(center=new_xyz, offset=obj.get_scale()[1], animate=time)
 

    config.callbackL = {
        ic.ICON_GIZMO_MOVE_3D: lambda: ars_window.viewport.controller.set_handles(["t"]),
        ic.ICON_GIZMO_SCALE: lambda: ars_window.viewport.controller.set_handles(["s"]),
        ic.ICON_GIZMO_ROTATE_3D: lambda: ars_window.viewport.controller.set_handles(["r"]),
        ic.ICON_GIZMO_DRAG: lambda: move_obj(),
    }

    config.callback_on_close = lambda: set_cursor("cursor")


    start_time = 0

    def start():
        nonlocal start_time
        start_time = time.time()
        ars_window.viewport.controller.set_handles([""]),

        if get_xyz(ars_window, ignore_objs=[obj]):
            ars_window.hotkey_manager._unbind_all()



    def during():
        if time.time() - start_time > 0.15:
            move_obj(False) # Should be False since we are updating continuously
            if get_cursor()[0] != "point":
                set_cursor("point", "bottom")

    
    def end():
        ars_window.ctx_key_active = False
        ars_window.ctx_key_last_end = time.time()
        set_cursor("cursor")
        try:
            if time.time() - start_time > 0.15:
                pass
                #ars_window.CF.UP(key="additional_text", value="Drag", auto_close = 500, symbol=ic.ICON_GIZMO_DRAG)
            else:
                open_context(config)
                set_cursor("point", "bottom")
        finally:
            ars_window.hotkey_manager._bind_shortcuts()



    key_check_continuous(callback=during,
                         key="Q",
                         interval=16,
                         callback_start=start,
                         callback_end=end
                         )