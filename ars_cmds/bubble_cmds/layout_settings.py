from ui.widgets.context_menu import ContextMenuConfig, open_context
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QPoint, Qt, QTimer
from theme.fonts.font_icons import *
import os
from PyQt6.QtWidgets import QFileDialog

def save_layout_as(main_window, path = None):
    # open "Save As" dialog
    if not path:
        path, _ = QFileDialog.getSaveFileName(
            main_window,                          # parent widget
            "Save Layout As",                     # dialog title
            os.path.join(os.getcwd(),"saved_layouts", "bubble_layout.arsl"),                                   # starting directory / default path
            "Layout Files (*.arsl *);;All Files (*)"  # file filter
        )

    # if user pressed cancel, path will be empty
    if path:
        main_window.bubbles_overlay.save_layout(path)



def BBL_MENU(main_window, position):
    config = ContextMenuConfig()

    options_list = [ICON_POWER, ICON_WINDOW_FULLSCREEN, ICON_SAVE,ICON_FILE_DOWNLOAD, ICON_LAYOUT]
    config.additional_texts = {
        ICON_POWER: "Close App",
        ICON_WINDOW_FULLSCREEN: "Minimize App",
        ICON_SAVE: "Save Layout",
        ICON_FILE_DOWNLOAD: "Save Layout As",
        ICON_LAYOUT: "Load Layout"
    }
    def toggle_fullscreen_maximized(main_window):
        if main_window.windowState() & Qt.WindowState.WindowFullScreen:
            # Currently fullscreen → switch to maximized
            main_window.setWindowState(Qt.WindowState.WindowMaximized)
        else:
            # Currently not fullscreen → switch to fullscreen
            main_window.setWindowState(Qt.WindowState.WindowFullScreen)
    config.callbackL = {
        ICON_POWER: lambda: QTimer.singleShot(250, lambda: main_window.close()),
        ICON_WINDOW_FULLSCREEN: lambda: toggle_fullscreen_maximized(main_window),
        ICON_SAVE: lambda: save_layout_as(main_window, os.path.join(os.getcwd(),"saved_layouts", "bubble_layout.arsl")),
        ICON_FILE_DOWNLOAD: lambda: save_layout_as(main_window, ),
        ICON_LAYOUT: lambda: main_window.bubbles_overlay.load_layout(os.path.join("saved_layouts", "bubble_layout.arsl")),
    }


    ctx = open_context(
        parent=main_window.central_widget,
        items=options_list,
        position=position,
        config=config
    )