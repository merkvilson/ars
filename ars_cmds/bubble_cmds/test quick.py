from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

from ars_cmds.core_cmds.load_object import add_sprite, selected_object

def BBL_5(self, position):
    run_ext(__file__, self)

def main(self):
    config = ContextMenuConfig()
    options_list = [
        ["1", "2", "3",],
    ]
    
    config.callbackL = {"1": lambda: add_sprite(self),
                        "2": lambda: print("Option 2 selected"),
                        "3": lambda: print("Option 3 selected"),
    }


    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    main(window)
