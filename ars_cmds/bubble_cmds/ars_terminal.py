from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from theme.fonts import font_icons as ic
from ui.ars_code import TerminalWidget

def BBL_CODE(*arg):
    run_ext(__file__)

def execute_cmd(ars_window):
    config = ContextMenuConfig()
    config.custom_width = ars_window.width()
    config.custom_height = 300
    config.auto_close = False
    config.close_on_outside = False
    items = ["   ", "terminal", "   "]
    terminal = TerminalWidget()
    terminal.setFixedSize(int(ars_window.width() - 10), int(config.custom_height - int(44 * 1.5)))
    config.custom_widget_items = {'terminal': terminal}

    ctx = open_context(config=config, items=items)
