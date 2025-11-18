from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext

def BBL_TEST2(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.show_value = True
    config.auto_close = False
    config.close_on_outside = False

    config.options = {
    "2": "Slider B",
    "1": "Slider A",
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


<<<<<<< HEAD
    ctx = open_context(config)
=======
    ctx = open_context(config)
>>>>>>> 82a8e21f2f7c15555cfbb5f355eae8670a62934b
