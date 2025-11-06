from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object
from PyQt6.QtCore import QPoint
from prefs.pref_controller import get_path
import os

BBL_TEST_CONFIG = {"symbol": ic.ICON_TEST}
def BBL_TEST(self, position):
    run_ext(__file__, self)

def main(self):

    config = ContextMenuConfig()

    config.slider_values = {
        'A': (0, 100, 50),
    }

    def set_img_by_index(val):
        val = int(val)
        images_path = get_path("frames")
        images_list = os.listdir(images_path)
        if images_list:
            # Map slider value (0-100) to image index (0 to len-1)
            max_index = len(images_list) - 1
            image_index = int((val / 100) * max_index)
            selected_image = images_list[image_index]
            image_path = os.path.join(images_path, selected_image)
        self.img.open_image(image_path)
    
    config.callbackL = {
        'A': lambda val: set_img_by_index(val),
        }


    ctx = open_context(
        parent=self.central_widget,
        items=['A'],
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    main(window)
