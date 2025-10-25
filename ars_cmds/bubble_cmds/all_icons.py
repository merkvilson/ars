from ui.widgets.context_menu import ContextMenuConfig, open_context
import pyperclip
from theme.fonts.new_fonts import get_font
from theme.fonts import font_icons as ic


def copy_name(self, k,v):
    pyperclip.copy(k)
    print(v)
    self.CF.UP("additional_text", k,  v, 1200)
 
def split_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]

BBL_ICONS_CONFIG={"symbol": ic.ICON_FILE_STACK}
def BBL_ICONS(self, position):
    config = ContextMenuConfig()
    config.item_radius = 25
    config.font = get_font(25)
    config.background_color = (30, 30, 30, 230)
    config.use_extended_shape = False
    options_list = split_list(ic.ICON_FULL_LIST, 10)

    vars_dict = {
        value: (lambda key=name, val=value: copy_name(self, key, val))
        for name, value in vars(ic).items()
        if isinstance(value, str) and value in ic.ICON_FULL_LIST
    }

    config.callbackL = vars_dict

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )

    return ctx