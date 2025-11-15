from ui.widgets.context_menu import ContextMenuConfig, open_context
from PyQt6.QtCore import Qt, QTimer
from theme.fonts import font_icons as ic
import os
from PyQt6.QtWidgets import QFileDialog
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

def save_layout_as(ars_window, path = None):
    # open "Save As" dialog
    if not path:
        path, _ = QFileDialog.getSaveFileName(
            ars_window,                          # parent widget
            "Save Layout As",                     # dialog title
            os.path.join(os.getcwd(),"saved_layouts", "bubble_layout.arsl"),                                   # starting directory / default path
            "Layout Files (*.arsl *);;All Files (*)"  # file filter
        )

    # if user pressed cancel, path will be empty
    if path:
        ars_window.bubbles_overlay.save_layout(path)



def BBL_MENU(*args):
    run_ext(__file__)



def execute_plugin(ars_window):
    config = ContextMenuConfig()

    options_list = [ic.ICON_POWER, ic.ICON_WINDOW_FULLSCREEN, ic.ICON_SAVE,ic.ICON_FILE_DOWNLOAD, ic.ICON_LAYOUT]
    config.additional_texts = {
        ic.ICON_POWER: "Close App",
        ic.ICON_WINDOW_FULLSCREEN: "Minimize App",
        ic.ICON_SAVE: "Save Layout",
        ic.ICON_FILE_DOWNLOAD: "Save Layout As",
        ic.ICON_LAYOUT: "Load Layout"
    }
    def toggle_fullscreen_maximized(ars_window):
        if ars_window.windowState() & Qt.WindowState.WindowFullScreen:
            # Currently fullscreen → switch to maximized
            ars_window.setWindowState(Qt.WindowState.WindowMaximized)
        else:
            # Currently not fullscreen → switch to fullscreen
            ars_window.setWindowState(Qt.WindowState.WindowFullScreen)
    config.callbackL = {
        ic.ICON_POWER: lambda: QTimer.singleShot(250, lambda: ars_window.close()),
        ic.ICON_WINDOW_FULLSCREEN: lambda: toggle_fullscreen_maximized(ars_window),
        ic.ICON_SAVE: lambda: save_layout_as(ars_window, os.path.join(os.getcwd(),"saved_layouts", "bubble_layout.arsl")),
        ic.ICON_FILE_DOWNLOAD: lambda: save_layout_as(ars_window, ),
        ic.ICON_LAYOUT: lambda: ars_window.bubbles_overlay.load_layout(os.path.join("saved_layouts", "bubble_layout.arsl")),
    }


    ctx = open_context(
        items=options_list,
        config=config
    )