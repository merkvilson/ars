from ui.widgets.context_menu import ContextMenuConfig, open_context
from PyQt6.QtGui import QCursor, QColor, QFont
from PyQt6.QtCore import QPoint, Qt, QTimer
from theme.fonts.font_icons import *
import os

from PyQt6.QtWidgets import QFileDialog

def load_bg_image(self, image_path = None):
    if image_path == None:
        image_path, _ = QFileDialog.getOpenFileName(None, "Select Background Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
    if image_path:
        self.viewport.bg.set_image(image_path)


BBL_RENDER_CONFIG = {"symbol": ICON_BACKGROUND}
def BBL_RENDER(self, position):
    config = ContextMenuConfig()

    options_list = [ICON_IMAGE,ICON_BACKGROUND,]

    config.additional_texts = {
        ICON_IMAGE: "Change BG",
        ICON_BACKGROUND: "Remove BG",    
        }



    config.callbackL = {
        ICON_IMAGE: lambda: load_bg_image(self),
        ICON_BACKGROUND: lambda: self.viewport.bg.clear_image(),
    }

    radial = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
