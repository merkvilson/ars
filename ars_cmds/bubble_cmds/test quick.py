from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor

from ars_cmds.core_cmds.load_object import add_sprite, selected_object
from ars_cmds.mesh_gen.animated_bbox import plane_fill_animation, delete_bbox_animations



def BBL_5(self, position):
    run_ext(__file__, self)

    
def main(self):
    
    if not selected_object(self):
        return
    else: obj = selected_object(self)

    obj.cutout()
    
    config = ContextMenuConfig()
    config.auto_close = False
    options_list = [
        ["1", "2", "3",],
    ]
    
    config.callbackL = {"1": lambda: plane_fill_animation(self.viewport._view.scene),
                        "2": lambda: delete_bbox_animations(self.viewport._view.scene),
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
