from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext



def BBL_TEST2(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.show_value = True

    config.options = {
    "1": "Slider A",
    "2": "Slider B",
    }

    config.slider_values = {
        "1": (0, 100, 50),
        "2": (0, 100, 50),

    }
    config.auto_close = False
    config.incremental_values = {
        "1": 1,
    }

    config.callbackL = {
        "1": lambda value: print(value),
        "2": lambda value: print(value),
    }

    ctx = open_context(config)
