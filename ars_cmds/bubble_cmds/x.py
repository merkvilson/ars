from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *
from ars_cmds.core_cmds.load_object import add_mesh

def BBL_X(self, position):
    config = ContextMenuConfig()
    options_list = ["X","Y","Z", "W"]

    om = self.viewport._objectManager

    index = om._active_idx
    if index < 0 or index >= len(om._objects):
        return
        
    obj = om._objects.pop(index)

    def clone_obj():
        self.viewport._objectManager.duplicate_selected()
        self.viewport._canvas.update()

    config.slider_values = {"Z": (0, 100, 30)}


    config.callbackL = {
        "X": lambda: clone_obj(),
        }
    
    config.additional_texts = {"X": "Clone object",
                               "Y": "Print bbox",
                               "Z": "Add mesh"}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )