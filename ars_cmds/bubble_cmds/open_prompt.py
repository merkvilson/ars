from ui.widgets.context_menu import ContextMenuConfig, open_context

from theme.fonts import font_icons as ic
from ui.widgets.multi_line_input import MultiLineInputWidget

BBL_PROMPT_CONFIG = {"symbol": ic.ICON_TEXT_INPUT, "hotkey": "P"}
def BBL_PROMPT(self, position):
    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
   # config.expand = "x"
    config.use_extended_shape = False
    config.distribution_mode = "y"
    config.anchor = "+y"

    options_list = [[ic.ICON_EYE,ic.ICON_EYE_CLOSED,ic.ICON_MENU], "A",]

    prompt_widget = MultiLineInputWidget(central_widget = self.central_widget)
    prompt_widget.setFixedSize(400, 140)

    config.custom_widget_items = {"A": prompt_widget}

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
