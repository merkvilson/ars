from ui.widgets.context_menu import ContextMenuConfig, open_context

from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor


from ars_cmds.obj_ctx.obj_prompt import prompt_ctx

BBL_PROMPT_CONFIG = {"symbol": ic.ICON_RENDER, "hotkey": "R"}
def BBL_PROMPT(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    prompt_ctx(ars_window, ars_window.central_widget.mapFromGlobal(QCursor.pos()), default_object= ars_window)