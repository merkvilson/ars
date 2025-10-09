#TODO: Fix hotkey toggle

from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *


def BBL_OBJ_BOX(self, position):
    config = ContextMenuConfig()
    config.auto_close = False
    config.show_value = True

    options_list = [ "1", "2", "A","B","C"]

    def test_function(self, value):
        obj = self.viewport._objectManager.get_selected_objects()[0]
        obj.set_color((value,0,value))

    def test_function2(self, value):
        obj = self.viewport._objectManager.get_selected_objects()[0]
        obj.set_scale((value,value,value))

    config.callbackL = {"1": lambda value: test_function(self,value/100),
                        "2": lambda value: test_function2(self,value/100),
                        }

    config.slider_values = {
    "1":(0,100,0),
    "2":(0,1000,1)
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
