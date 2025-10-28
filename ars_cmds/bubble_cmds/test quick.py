from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

from ars_cmds.core_cmds.load_object import add_sprite, selected_object
from ars_cmds.mesh_gen.animated_bbox import plane_fill_animation, delete_bbox_animations



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
    

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

    # def doit(): print("doit")
    
    # # Store the original closeEvent method
    # original_closeEvent = ctx.closeEvent
    
    # # Create a new closeEvent function
    # def new_closeEvent(event):
    #     doit()  # Call your function
    #     original_closeEvent(event)  # Call the original event handler
    
    # # Replace the widget's closeEvent with your new one
    # ctx.closeEvent = new_closeEvent

def execute_plugin(window):
    main(window)
