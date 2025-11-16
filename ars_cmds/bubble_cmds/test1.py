from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from theme.fonts import font_icons as ic

def BBL_TEST(*args): run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.options = {
        ic.ICON_TEST: "Option A",
        ic.ICON_TEST2: "Option B",
        ic.ICON_TEST3: "Option C",}
    ctx = open_context(config)