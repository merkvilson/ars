from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic


BBL_TEST_CONFIG ={"symbol": ic.ICON_TEST }
def BBL_TEST(self, position):
    config = ContextMenuConfig()


    options_list = [
        ["1", "2", "3"],
    ]
 

    config.additional_texts = {
    "1": "Option 1",
    "2": "Option 2",
    "3": "Option 3",
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
