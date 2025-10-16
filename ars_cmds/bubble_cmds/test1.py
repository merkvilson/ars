from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

BBL_TEST_CONFIG = {"symbol": ic.ICON_TEST}
def BBL_TEST(self, position):
    run_ext(__file__, self)

def main(self):
    config = ContextMenuConfig()
    options_list = [
        ["1", "2", "3", "4", "5"],
    ]
    

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    main(window)
