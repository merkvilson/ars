from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic

from PyQt6.QtWidgets import QFileDialog

def load_bg_image(self, image_path = None):
    if image_path == None:
        image_path, _ = QFileDialog.getOpenFileName(None, "Select Background Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
    if image_path:
        self.viewport.bg.set_image(image_path)


BBL_RENDER_CONFIG = {"symbol": ic.ICON_BACKGROUND}
def BBL_RENDER(self, position):
    config = ContextMenuConfig()

    options_list = [ic.ICON_IMAGE,ic.ICON_BACKGROUND,]

    config.additional_texts = {
        ic.ICON_IMAGE: "Change BG",
        ic.ICON_BACKGROUND: "Remove BG",    
        }



    config.callbackL = {
        ic.ICON_IMAGE: lambda: load_bg_image(self),
        ic.ICON_BACKGROUND: lambda: self.viewport.bg.clear_image(),
    }

    radial = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
