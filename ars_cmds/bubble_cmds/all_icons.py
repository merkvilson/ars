from ui.widgets.context_menu import ContextMenuConfig, open_context
import pyperclip
from theme.fonts.new_fonts import get_font
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
#TODO; Popup name during hover
def copy_name(ars_window, k,v):
    pyperclip.copy(k)
    ars_window.CF.UP("additional_text", k,  v, 1200)
 
def split_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]

BBL_ICONS_CONFIG={"symbol": ic.ICON_FILE_STACK}
def BBL_ICONS(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = ContextMenuConfig()
    config.item_radius = 25
    config.font = get_font(25)
    config.background_color = (30, 30, 30, 230)
    config.use_extended_shape = False
    options_list = split_list(ic.ICON_FULL_LIST, 10)

    config.callbackL = {
        value: (lambda key=name, val=value: copy_name(ars_window, key, val))
        for name, value in vars(ic).items()
        if isinstance(value, str) and value in ic.ICON_FULL_LIST
    }

    config.callback_hover_in = {
        value: (lambda key=name, val=value: ars_window.msg(key))
        for name, value in vars(ic).items()
        if isinstance(value, str) and value in ic.ICON_FULL_LIST
    }

    ctx = open_context(
        items=options_list,
        config=config
    )