"""
Object Duplication Command Module
=================================

This module implements the "Duplicate Object" functionality, allowing users to quickly clone selected 3D objects.

Functionality:
--------------
- **Activation**: Triggered by the configured hotkey (Default: 'Ctrl+D').
- **Duplication**: 
    - Creates an exact copy of the currently selected object using the object manager.
    - The new copy becomes the active selection.
- **Placement**: 
    - Immediately after duplication, the clone is animated to the current cursor position in 3D space.
    - This prevents the clone from overlapping perfectly with the original, making it visible immediately.
- **Visual/Audio Feedback**:
    - Plays a "pop-clear" sound effect on activation.
    - Temporarily hides gizmo handles to reduce visual clutter during the move.

Key Components:
---------------
- `BBL_2_CONFIG`: Configuration for the bubble command (Icon, Hotkey).
- `execute_cmd`: Main logic wrapper.
    - Checks for selection.
    - Calls `ars_window.viewport._objectManager.duplicate_selected()`.
    - Calculates new position using `get_xyz` and moves the clone.

Dependencies:
-------------
- `ars_cmds.core_cmds`: For object selection and coordinate conversion.
- `core`: For sound management.
"""
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from core.sound_manager import play_sound

BBL_2_CONFIG = {"symbol": ic.ICON_FILES, "hotkey": "Ctrl+D", "hidden": True}


def BBL_2(*args):
    run_ext(__file__)


def execute_cmd(ars_window):

    #Todo: during cloning animation color may be also cloned. need to add delay.

    original = selected_object()
    if not original:
        return

    play_sound("pop-clear", 0.05)

    ars_window.viewport._objectManager.duplicate_selected()

    # After duplication, the clone becomes selected.
    clone = selected_object()
    if not clone or clone is original:
        return

    new_xyz = get_xyz(ars_window)
    if new_xyz:
        clone.move_to(center=new_xyz, offset=clone.get_scale()[1], animate=0.25)

    ars_window.viewport.controller.set_handles([""])
