from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext


BBL_TEST_CONFIG ={"symbol": ic.ICON_TEST }
def BBL_TEST(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    config = ContextMenuConfig()
    config.custom_height = 300
    config.auto_close = False
    config.close_on_outside = False
    config.custom_width = ars_window.width()

    #todo add browser_widget
    # config.custom_widget_items = {'browser_widget': }

    options_list = [
        ["browser_widget"],
    ]

    ctx = open_context(
        items=options_list,
        config=config
    )

