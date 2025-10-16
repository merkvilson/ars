from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from PyQt6.QtGui import QCursor
import theme.fonts.new_fonts as RRRFONT


def obj_scale(self, position):

    obj = self.viewport._objectManager.get_selected_objects()
    if not obj:
        return
    
    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return
    obj = selected[0]


    config = ContextMenuConfig()
    #config.auto_close = True
    config.close_on_outside = False
    config.item_radius = 14
    config.font = RRRFONT.get_font(14)
    config.auto_close = True
    config.extra_distance = [0,-150]

    options_list = [
        ["1", "2", "3"],
    ]

    config.slider_values = {
        "1": (1,100,obj.get_scale()[0]*100),
        "2": (1,100,obj.get_scale()[1]*100),
        "3": (1,100,obj.get_scale()[2]*100),}
    
    config.callbackL = {
        "1": lambda value: obj.set_scale((value/100, obj.get_scale()[1], obj.get_scale()[2])),
        "2": lambda value: obj.set_scale((obj.get_scale()[0], value/100, obj.get_scale()[2])),
        "3": lambda value: obj.set_scale((obj.get_scale()[0], obj.get_scale()[1], value/100)), 
    }
    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
