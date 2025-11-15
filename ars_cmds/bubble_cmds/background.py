from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from PyQt6.QtWidgets import QFileDialog
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor


def load_bg_image(ars_window, image_path = None):
    if image_path == None:
        image_path, _ = QFileDialog.getOpenFileName(None, "Select Background Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
    if image_path:
        ars_window.viewport.bg.set_image(image_path)


BBL_RENDER_CONFIG = {"symbol": ic.ICON_BACKGROUND}
def BBL_RENDER(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()

    options_list = [ic.ICON_IMAGE,ic.ICON_BACKGROUND,]

    config.additional_texts = {
        ic.ICON_IMAGE: "Change BG",
        ic.ICON_BACKGROUND: "Remove BG",    
        }



    config.callbackL = {
        ic.ICON_IMAGE: lambda: load_bg_image(ars_window),
        ic.ICON_BACKGROUND: lambda: ars_window.viewport.bg.clear_image(),
    }

    radial = open_context(
        items=options_list,
        config=config
    )
