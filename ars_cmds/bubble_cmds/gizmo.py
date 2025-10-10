from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *


BBL_GIZMO_MOVE_CONFIG = {"symbol": ICON_GIZMO_MOVE, "hotkey": "Q"}
def BBL_GIZMO_MOVE(self, position):
    config = ContextMenuConfig()


    options_list = [ICON_GIZMO_MOVE_3D, ICON_GIZMO_SCALE, ICON_GIZMO_ROTATE_3D, ICON_GIZMO_DRAG]

    config.callbackL = {

        ICON_GIZMO_MOVE_3D:   lambda:(self.viewport.controller.set_handles(['t'])),
        ICON_GIZMO_SCALE:     lambda:(self.viewport.controller.set_handles(['s'])),
        ICON_GIZMO_ROTATE_3D: lambda:(self.viewport.controller.set_handles(['r'])),
        ICON_GIZMO_DRAG: lambda:(self.viewport.controller.set_handles(['tzx'])),
    }


    config.toggle_values = {
    ICON_GIZMO_MOVE_3D:   (0,1,self.viewport.controller.get_visibility("move")),
    ICON_GIZMO_SCALE:     (0,1,self.viewport.controller.get_visibility("scale")),
    ICON_GIZMO_ROTATE_3D: (0,1,self.viewport.controller.get_visibility("rotate")),
    ICON_GIZMO_DRAG: (0,1,0),
}

    config.toggle_groups = [options_list]

    config.hotkey_items = {
        ICON_GIZMO_MOVE_3D:   "W",
        ICON_GIZMO_SCALE:     "E",
        ICON_GIZMO_ROTATE_3D: "R",
    }


    config.additional_texts = {
        ICON_GIZMO_MOVE_3D: "Move",
        ICON_GIZMO_ROTATE_3D: "Rotate",
        ICON_GIZMO_SCALE: "Scale",
        ICON_GIZMO_DRAG: "New Gizmo",
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )