from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object
from PyQt6.QtCore import QPoint

BBL_TEST_CONFIG = {"symbol": ic.ICON_TEST}
def BBL_TEST(self, position):
    run_ext(__file__, self)

def main(self):
    if not selected_object(self):
        return
    else: obj = selected_object(self)
    
    obj.set_shading(None)

def execute_plugin(window):
    main(window)
