"""
Camera View Control Module
==========================

This module implements smart camera focusing functionality, allowing users to quickly navigate the 3D view
based on context and input duration. It distinguishes between a "Short Press" and a "Long Press" of the hotkey
to trigger different focusing behaviors.

Functionality:
--------------
- **Activation**: Triggered by the configured hotkey (Default: 'V').
- **Short Press (< 0.15s)**: Focus on Selection.
    - Centers the camera on the currently selected object.
    - Adjusts the zoom distance based on the object's scale.
    - Resets camera rotation to default.
    - If no object is selected, resets the view to the "Home" position (0,0,0).
- **Long Press (> 0.15s)**: Focus on Cursor.
    - Centers the camera on the 3D point directly under the mouse cursor (raycast).
    - Useful for quickly navigating to a specific part of the scene or grid.
- **Visual Feedback**:
    - The cursor changes to a "map-pin" icon during a long press to indicate that the "Focus on Cursor" mode is active.

Key Components:
---------------
- `BBL_CAMVIEWER_CONFIG`: Configuration for the bubble command.
- `execute_cmd`: Main logic wrapper.
    - `view_cursor`: Logic to raycast and move camera to cursor position.
    - `view_selected`: Logic to move camera to selected object or home.
    - `start`, `during`, `end`: Callbacks for `key_check_continuous` that measure press duration and trigger the appropriate action.

Dependencies:
-------------
- `ars_cmds.core_cmds`: For object selection and coordinate conversion.
- `core`: For cursor management.
- `vispy` (via `ars_window.viewport.cam`): For camera manipulation.
"""
from ars_cmds.core_cmds.run_ext import run_ext
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object as get_selected
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from ars_cmds.core_cmds.key_check import key_check_continuous
from core.cursor_modifier import get_cursor, set_cursor
import time

from util_functions.ars_window import ars_window as ars_wind

BBL_CAMVIEWER_CONFIG = {"symbol": ic.ICON_WINDOW_MINIMIZE, "hotkey": "V", "hidden": True}


def BBL_CAMVIEWER(*args):
    run_ext(__file__)



def view_selected():
    camera = ars_wind().viewport.cam
    obj = get_selected()
    if not obj: 
        view_home()
        return
    xyz=obj.get_position()
    scale_sum = sum(obj.get_scale()) * 1.5
    default_rotation = (camera._reset_rotation1, camera._reset_rotation2)

    camera.move_to(center=tuple(xyz), offset=scale_sum, animate=True, rotation=default_rotation)

def view_home():
    camera = ars_wind().viewport.cam
    default_rotation = (camera._reset_rotation1, camera._reset_rotation2)
    camera.move_to(center=(0,0,0), offset=10, animate=True, rotation=default_rotation)
    



def execute_cmd(ars_window):
    if getattr(ars_window, "ctx_key_active", False):return
    if time.time() - getattr(ars_window, "ctx_key_last_end", 0) < 0.2:return
    ars_window.ctx_key_active = True

    camera = ars_window.viewport.cam


    def view_cursor():
        new_xyz = get_xyz(ars_window)
        
        camera.move_to(center=new_xyz, offset=5 if new_xyz else -15, animate=True)


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
            if time.time() - start_time > 0.15:  view_cursor()
            else: view_selected()
        finally:
            ars_window.hotkey_manager._bind_shortcuts()



    key_check_continuous(callback=during,
                         key="V",
                         interval=16,
                         callback_start=start,
                         callback_end=end,
                         )
