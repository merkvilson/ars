from ui.widgets.context_menu import ContextMenuConfig, open_context
from PyQt6.QtGui import QCursor, QColor
from PyQt6.QtCore import QPoint, Qt, QTimer
from theme.fonts import font_icons as ic
import pyperclip
from theme.fonts.new_fonts import get_font

def copy_name(self, k,v):
    pyperclip.copy(k)
    print(v)
    self.CF.UP("additional_text", k,  v, 1200)
 

def split_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]




BBL_ICONS_CONFIG={"symbol": ic.ICON_FILE_STACK}
def BBL_ICONS(self, position):
    config = ContextMenuConfig()
    config.use_extended_shape = False
    options_list = split_list(ic.ICON_FULL_LIST, 10)



    vars_dict = {
    v: (lambda key=k, value=v: copy_name(self, key, value))
    for k, v in globals().items()
    if v in ic.ICON_FULL_LIST
}

    config.callbackL = vars_dict

    mouse_pos = self.central_widget.mapFromGlobal(QCursor.pos())
    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=mouse_pos,
        config=config
    )