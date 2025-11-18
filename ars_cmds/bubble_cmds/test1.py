from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from theme.fonts import font_icons as ic
from ui.widgets.screen_color_picker import ScreenshotOverlay
from PyQt6.QtWidgets import QApplication

def BBL_TEST(*args): run_ext(__file__)

def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
    config.options = {
        ic.ICON_TEST: "Option A",
        ic.ICON_TEST2: "Option B",
        ic.ICON_TEST3: "Color Picker",}
    

    def display_color_callback(color):
        ctx.update_item(ic.ICON_TEST3, "color", color)

    def start_picking(ctx):
        
        # Capture entire screen
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        ctx.overlay = ScreenshotOverlay(screenshot, paretn_callback=display_color_callback)

    config.callbackL = { ic.ICON_TEST3: lambda: start_picking(ctx),}

    ctx = open_context(config)