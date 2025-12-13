from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from core.sound_manager import play_sound

BBL_2_CONFIG = {"symbol": ic.ICON_FILES, "hotkey": "Ctrl+D", "hidden": True}


def BBL_2(*args):
    run_ext(__file__)


def execute_cmd(ars_window):

    obj = selected_object()
    if not obj:
        return

    play_sound("pop-clear", 0.05)

    ars_window.viewport._objectManager.duplicate_selected()

    new_xyz = get_xyz(ars_window, ignore_objs=[obj])
    if new_xyz:
        obj.move_to(center=new_xyz, offset=obj.get_scale()[1], animate=0.25)

    ars_window.viewport.controller.set_handles([""])
