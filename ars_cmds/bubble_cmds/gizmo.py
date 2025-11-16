from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

BBL_GIZMO_MOVE_CONFIG = {"symbol": ic.ICON_GIZMO_MOVE, "hotkey": "Q"}
def BBL_GIZMO_MOVE(*args):
    run_ext(__file__)



def execute_plugin(ars_window):
    if not selected_object():
        return

    config = ContextMenuConfig()


    options_list = [ic.ICON_GIZMO_MOVE_3D, ic.ICON_GIZMO_SCALE, ic.ICON_GIZMO_ROTATE_3D, ic.ICON_GIZMO_DRAG]

    config.callbackL = {

        ic.ICON_GIZMO_MOVE_3D:   lambda:(ars_window.viewport.controller.set_handles(['t'])),
        ic.ICON_GIZMO_SCALE:     lambda:(ars_window.viewport.controller.set_handles(['s'])),
        ic.ICON_GIZMO_ROTATE_3D: lambda:(ars_window.viewport.controller.set_handles(['r'])),
        ic.ICON_GIZMO_DRAG: lambda:(ars_window.viewport.controller.set_handles(['qq'])),
    }


    config.toggle_values = {
    ic.ICON_GIZMO_MOVE_3D:   (0,1,ars_window.viewport.controller.get_visibility("move")),
    ic.ICON_GIZMO_SCALE:     (0,1,ars_window.viewport.controller.get_visibility("scale")),
    ic.ICON_GIZMO_ROTATE_3D: (0,1,ars_window.viewport.controller.get_visibility("rotate")),
    ic.ICON_GIZMO_DRAG: (0,1,0),
}

    config.toggle_groups = [options_list]

    config.hotkey_items = {
        ic.ICON_GIZMO_MOVE_3D:   "W",
        ic.ICON_GIZMO_SCALE:     "E",
        ic.ICON_GIZMO_ROTATE_3D: "R",
        ic.ICON_GIZMO_DRAG: "Q",
    }


    config.additional_texts = {
        ic.ICON_GIZMO_MOVE_3D: "Move",
        ic.ICON_GIZMO_ROTATE_3D: "Rotate",
        ic.ICON_GIZMO_SCALE: "Scale",
        ic.ICON_GIZMO_DRAG: "New Gizmo",
    }

    ctx = open_context(
        items=options_list,
        config=config
    )
    ctx.symbol = ic.ICON_GIZMO_MOVE