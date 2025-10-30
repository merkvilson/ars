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
    options_list = ["1", "2", "3", "4", "5", "6", "7"]


    config = ContextMenuConfig()
    config.auto_close = False
    #'sphere', 'cube', 'plane', 'cylinder', 'cone', 'disc'

    config.callbackL={"1": lambda: obj.set_primitive_type('sphere'),
                     "2": lambda: obj.set_primitive_type('cube'),
                     "3": lambda: obj.set_primitive_type('plane'),
                     "4": lambda: obj.set_primitive_type('cylinder'),
                     "5": lambda: obj.set_primitive_type('disc'),
                     "6": lambda: obj.set_primitive_type('cone'),
                     }


    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=QPoint(0, 0),
        config=config
    )



def execute_plugin(window):
    main(window)
