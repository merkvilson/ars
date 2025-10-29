from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object



def BBL_5(self, position):
    run_ext(__file__, self)

    
def main(self):
    
    if not selected_object(self):
        return
    else: obj = selected_object(self)

    obj.set_text("Quick Bubble")


def execute_plugin(window):
    main(window)
