from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object
from PyQt6.QtCore import QPoint, QTimer


BBL_TEST_CONFIG ={"symbol": ic.ICON_TEST }
def BBL_TEST(self, position):
    run_ext(__file__, self)


def main(self, position):
    config = ContextMenuConfig()


    options_list = [
        ["1", "2"],
    ]
 

    config.additional_texts = {
    "1": "Button 1",
    "2": "Button 2",
    }

    config.callbackL = {
        "1": lambda: print("Button 1 pressed"),
        "2": lambda: print("Button 2 pressed"),
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )


def execute_plugin(window):
    main(window, position=window.central_widget.mapFromGlobal(QCursor.pos()))
