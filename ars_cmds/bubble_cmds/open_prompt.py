from ui.widgets.context_menu import ContextMenuConfig, open_context

from theme.fonts import font_icons as ic
# from ui.widgets.multi_line_input import MultiLineInputWidget

from ars_cmds.obj_ctx.obj_prompt import prompt_ctx

BBL_PROMPT_CONFIG = {"symbol": ic.ICON_TEXT_INPUT, "hotkey": "P"}
def BBL_PROMPT(self, position, default_object = None):

    prompt_ctx(self, position, default_object= self)
