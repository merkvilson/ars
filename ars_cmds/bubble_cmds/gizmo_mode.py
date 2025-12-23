"""
Gizmo Move Command Module
=========================

This module implements the "Gizmo Move" functionality, allowing users to interactively move and rotate 
selected 3D objects using a hotkey-driven workflow.

Functionality:
--------------
- **Activation**: Triggered by the configured hotkey (Default: 'Q').
- **Object Movement**: 
    - On initial press, the selected object animates to the cursor's 3D position.
    - While holding the key, the object continuously follows the cursor in 3D space.
    - Uses raycasting (`get_xyz`) to determine the 3D position on the grid or other objects.
- **Parenting**: 
    - Automatically reparents the selected object if dropped onto another object.
    - Unparents if dropped on the grid or background.
- **Rotation**: 
    - Mouse scroll while holding the hotkey rotates the object around the Y-axis in 15-degree increments.
    - Provides visual feedback of the current rotation angle.
- **Visual/Audio Feedback**:
    - Changes cursor style during operation.
    - Plays sound effects on activation and rotation.
    - Hides standard gizmo handles during the move operation.

Key Components:
---------------
- `BBL_GIZMO_MOVE_CONFIG`: Configuration for the bubble command (Icon, Hotkey, Visibility).
- `execute_cmd`: Main logic wrapper setting up the continuous key check and state management.
    - `move_obj`: Handles the logic for calculating position and setting parent relationships.
    - `start`, `during`, `end`, `scroll`: Callbacks for the `key_check_continuous` input loop.

Dependencies:
-------------
- `ars_cmds.core_cmds`: For object selection, input handling, and coordinate conversion.
- `core`: For cursor management and sound effects.
- `PyQt6`: For timer-based delayed actions.
"""
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.key_check import key_check_continuous
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from core.cursor_modifier import get_cursor, set_cursor
import time
from core.sound_manager import play_sound
from PyQt6.QtCore import QTimer

BBL_GIZMO_MOVE_CONFIG = {"symbol": ic.ICON_GIZMO_MOVE, "hotkey": "Q", "visible": False}


def BBL_GIZMO_MOVE(*args):
    run_ext(__file__)


def execute_cmd(ars_window):

    obj = selected_object()
    if not obj:
        return

    if getattr(ars_window, "ctx_key_active", False):return
    if time.time() - getattr(ars_window, "ctx_key_last_end", 0) < 0.2:return
    ars_window.ctx_key_active = True


    
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

    def scroll(value):
        play_sound("click") #Need to choose another sound for rotation
        angle_deg = 15 * (1 if value > 0 else -1)

        obj.rotate_around_axis((0, 1, 0), angle_deg)
        ars_window.CF.UP(key="additional_text", value=str(int(obj.get_rotation()[1]))+"°", auto_close = 1000,symbol=ic.ICON_VIEW_360_ARROW)



    key_check_continuous(callback=during,
                         key="Q",
                         interval=16,
                         callback_start=start,
                         callback_end=end,
                         scroll_callback=scroll
                         )
