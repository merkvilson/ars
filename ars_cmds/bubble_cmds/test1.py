from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from theme.fonts import font_icons as ic
from ui.widgets.screen_color_picker import ScreenColorPicker, ScreenshotOverlay
from PyQt6.QtWidgets import QApplication

def BBL_TEST(*args): run_ext(__file__)

def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
    config.options = {
        "ScreenColorPicker": "ScreenColorPicker",
        ic.ICON_TEST: "Option A",
        ic.ICON_TEST2: "Option B",
        ic.ICON_TEST3: "Option C",}
    
    color_picker = ScreenColorPicker()
    config.inner_widgets = {"ScreenColorPicker": color_picker,}



    ctx = open_context(config)