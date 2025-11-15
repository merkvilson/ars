from ui.widgets.context_menu import ContextMenuConfig, open_context
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, QTimer
from theme.fonts import font_icons as ic
import theme.fonts.new_fonts as RRRFONT

def unlock_function(self):
    new_state = Qt.CheckState.Unchecked if self.bubbles_overlay.locked else Qt.CheckState.Checked
    self.bubbles_overlay.toggle_lock(new_state.value)




def r_dropdown(self):
    config = ContextMenuConfig()
    config.item_radius = 15
    config.font = RRRFONT.get_font(15)
    config.use_extended_shape = True
    config.auto_close = True
    config.close_on_outside = True

    ic.ICON_LOCK_state = ic.ICON_LOCK if self.bubbles_overlay.locked else ic.ICON_LOCK_OPEN

    
    options_list = [
        ic.ICON_LOCK_state,
        "?",
        ic.ICON_MENU,
        ic.ICON_PIN,
        ic.ICON_CODE_TERMINAL,
        ic.ICON_POWER,
    ]

    config.toggle_values = {
            ic.ICON_LOCK_state: not self.bubbles_overlay.locked,
    }

    config.callbackL = {
        ic.ICON_LOCK_state:  lambda: (
                               unlock_function(self),
                               ctx.update_item(ic.ICON_LOCK_state, "symbol", ic.ICON_LOCK if self.bubbles_overlay.locked else ic.ICON_LOCK_OPEN),
            ),
        ic.ICON_POWER: lambda: QTimer.singleShot(500, self.close),
    }



    config.additional_texts = {
        ic.ICON_LOCK_state: "Edit",
        "?": "Help",
        ic.ICON_MENU: "Settings",
        ic.ICON_PIN: "Pin",
        ic.ICON_CODE_TERMINAL: "Edit Code",
        ic.ICON_POWER: "Exit",
    }



    ctx = open_context(
        items=options_list,
        config=config
    )