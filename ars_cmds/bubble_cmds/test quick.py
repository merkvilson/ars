from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.load_object import selected_object
from ui.widgets.multi_line_input import MultiLineInputWidget
from PyQt6.QtCore import QPoint



def BBL_TEST2(self, position):
    run_ext(__file__, self)

    
def main(self, position):
    config = ContextMenuConfig()

    options_list = [ "a", "b", "c" ]


    config.callbackL = {"a": lambda: print("Option A selected"),
                        "b": lambda: print("Option B selected"),
                        "c": lambda: print("Option C selected")}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )



def execute_plugin(window):
    main(window, QPoint(0, 0))













