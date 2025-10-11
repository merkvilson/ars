from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *
from ars_cmds.core_cmds.load_object import add_mesh

def BBL_X(self, position):
    config = ContextMenuConfig()
    
    options_list = ["X","Y","Z"]

    print(self)

    def clone_obj():
        self.viewport._objectManager.duplicate_selected()
        self.viewport._canvas.update()


    config.callbackL = {"X": lambda: clone_obj(),
                        "Z": lambda: print("Z selected")}
    
    config.additional_texts = {"X": "Clone selected object(s)",}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )