
"""This module provides gizmo control functionality (move) via hotkey hold."""
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.key_check import key_check_continuous
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from core.cursor_modifier import get_cursor, set_cursor
import time
from core.sound_manager import play_sound
from PyQt6.QtCore import QTimer

BBL_2_CONFIG = {"symbol": ic.ICON_FILES, "hotkey": "Ctrl+D", "hidden": True}


def BBL_2(*args):
    run_ext(__file__)


def execute_cmd(ars_window):

    obj = selected_object()
    if not obj:
        return

    if getattr(ars_window, "ctx_key_active", False):return
    if time.time() - getattr(ars_window, "ctx_key_last_end", 0) < 0.2:return
    ars_window.ctx_key_active = True


    ars_window.viewport._objectManager.duplicate_selected()

    
    def move_obj(time=0.25):
        def cb_obj(target_obj):
            if target_obj != obj:
                if time:
                    QTimer.singleShot(int(time * 1000), lambda: obj.set_parent(target_obj))
                else:
                    obj.set_parent(target_obj)
        
        def cb_none():
            if time:
                QTimer.singleShot(int(time * 1000), lambda: obj.set_parent(None))
            else:
                obj.set_parent(None)

        new_xyz = get_xyz(ars_window, ignore_objs=[obj], callback_object=cb_obj, callback_grid=cb_none, callback_background=cb_none)
        if new_xyz:
            obj.move_to(center=new_xyz, offset=obj.get_scale()[1], animate=time)


    def start():
        # One-shot animated move on initial key press
        ars_window._gizmo_move_press_time = time.time()
        move_obj(0.25)
        set_cursor("point", "center")
        play_sound("pop-clear", 0.05)
        ars_window.viewport.controller.set_handles([""])


    def during():
        # Start continuous dragging only after the initial 0.25s move
        if time.time() - getattr(ars_window, "_gizmo_move_press_time", 0) < 0.25:
            return
        move_obj(False)  # Should be False since we are updating continuously
    
    def end():
        ars_window.ctx_key_active = False
        ars_window.ctx_key_last_end = time.time()
        ars_window._gizmo_move_press_time = 0
        set_cursor("cursor")

        QTimer.singleShot(int(0.25 * 1000), lambda: obj.pick())  # Re-select the object after move animation

    def scroll(value):
        play_sound("click") #Need to choose another sound for rotation
        angle_deg = 15 * (1 if value > 0 else -1)

        obj.rotate_around_axis((0, 1, 0), angle_deg)
        ars_window.CF.UP(key="additional_text", value=str(int(obj.get_rotation()[1]))+"°", auto_close = 1000,symbol=ic.ICON_VIEW_360_ARROW)



    key_check_continuous(callback=during,
                         key="D",
                         interval=16,
                         callback_start=start,
                         callback_end=end,
                         scroll_callback=scroll
                         )
