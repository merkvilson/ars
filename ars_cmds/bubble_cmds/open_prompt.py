from ui.widgets.context_menu import ContextMenuConfig, open_context

from theme.fonts import font_icons as ic
# from ui.widgets.multi_line_input import MultiLineInputWidget



BBL_PROMPT_CONFIG = {"symbol": ic.ICON_TEXT_INPUT, "hotkey": "P"}
def BBL_PROMPT(self, position, default_object = None):

    print("Opening prompt context menu")
    #TODO: Refactor to use MultiLineInputWidget
