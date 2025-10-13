from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import os
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import add_mesh

def BBL_2(self, position):
    run_ext(__file__, self)

def doit(self):
    config = ContextMenuConfig()
    options_list = [
        ["1", "2", "3", "4"],
    ]
 

    config.additional_texts = {
    "1": "Option 1",
    "2": "Option 2",
    "3": "Option 3",
    }

    config.callbackL = {"1": lambda: add_mesh(self, os.path.join("res","mesh files", 'box.obj'      ), animated = False)}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

def execute_plugin(window):
    doit(window)
