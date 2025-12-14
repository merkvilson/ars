from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from core.sound_manager import play_sound

BBL_2_CONFIG = {"symbol": ic.ICON_FILES, "hotkey": "Ctrl+D", "hidden": True}


def BBL_2(*args):
    run_ext(__file__)


def execute_cmd(ars_window):

    originals = ars_window.viewport._objectManager.get_selected_objects()
    if not originals:
        return

    play_sound("pop-clear", 0.05)

    ars_window.viewport._objectManager.duplicate_selected()

    # After duplication, selection becomes the newly created clone(s).
    # Filter out originals just in case.
    originals_ids = {id(o) for o in originals}
    clones = [o for o in ars_window.viewport._objectManager.get_selected_objects() if id(o) not in originals_ids]
    if not clones:
        return

    new_xyz = get_xyz(ars_window, ignore_objs=[*originals, *clones])
    if new_xyz:
        # Minimal behavior: move the first clone to cursor.
        clones[0].move_to(center=new_xyz, offset=clones[0].get_scale()[1], animate=0.25)

    ars_window.viewport.controller.set_handles([""])
