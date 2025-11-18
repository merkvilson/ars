from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext

from ui.widgets.screen_color_picker import ScreenshotOverlay
from PyQt6.QtWidgets import QApplication


def BBL_TEST2(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.show_value = True
    config.auto_close = False
    config.close_on_outside = False

    config.options = {
    "1": "Slider A",
    "2": "Slider B",
    ic.ICON_COLOR_PICKER: "Color Picker"
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
        ic.ICON_COLOR_PICKER: lambda: start_picking(ctx),
    }


    def display_color_callback(color):
        ctx.update_item(ic.ICON_COLOR_PICKER, "color", color)

    def start_picking(ctx):
        
        # Capture entire screen
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        ctx.overlay = ScreenshotOverlay(screenshot, paretn_callback=display_color_callback)

    ctx = open_context(config)
