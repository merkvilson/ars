from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.key_check import key_check_continuous
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz

BBL_CURSOR_XYZ_CONFIG = {"symbol": ic.ICON_OBJ_CIRCLE, "hotkey": "X"}

def BBL_CURSOR_XYZ(*args):
    """Entry point for the cursor to XYZ command."""
    run_ext(__file__)

def execute_cmd(ars_window):
    """
    Executes the command to move the selected object to the cursor's 3D position.
    
    Args:
        ars_window: The main application window instance.
    """
    ars_window.hotkey_manager._unbind_all()
    obj = selected_object()
    if not obj:
        return
    xyz = get_xyz(ars_window)
    if xyz:
        # obj.set_position(*xyz)
        key_check_continuous(
            callback=lambda:(obj.set_position(*xyz), print(f"XYZ: {xyz}")), 
            callback_end=lambda: (ars_window.hotkey_manager._bind_shortcuts(),print("binded")), 
            key='x', 
            interval=100)
