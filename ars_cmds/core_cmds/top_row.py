from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic


def execute_cmd(ars_window):
    config = CtxConfig()
    config.dock_area = "top"
    config.auto_close = False
    config.close_on_outside = False
    config.use_extended_shape = False
    config.distribution_mode = "x"


    items = [ ic.ICON_SETTINGS, ic.ICON_LIST, "   ", ic.ICON_CAMERA, ic.ICON_EYE, ic.ICON_RENDER, ic.ICON_BRAIN, ic.ICON_OBJ_BBOX, ic.ICON_CODE_TERMINAL, ic.ICON_WORKFLOW, ic.ICON_BACKGROUND,ic.ICON_PLAYER_TRACK_NEXT, "   ",  ic.ICON_BUBBLE,ic.ICON_MENU,]


    
    
    ctx = config.open_context(parent=ars_window.central_widget, items=items)

