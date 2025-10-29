from ui.widgets.context_menu import ContextMenuConfig, open_context
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor




def BBL_5(self, position):
    run_ext(__file__, self)

    
def main(self):
    
    # if not selected_object(self):
    #     return
    # else: obj = selected_object(self)

    
    
    config = ContextMenuConfig()
    config.auto_close = False
    options_list = [
        ["1", "2", "3",],
    ]
    
    def doit(): print("doit")
    config.callback_on_close = doit

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )


def execute_plugin(window):
    main(window)
