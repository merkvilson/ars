from ui.widgets.context_menu import ContextMenuConfig, open_context
from PyQt6.QtGui import QCursor, QColor, QFont
from PyQt6.QtCore import QPoint, Qt, QTimer
from theme.fonts.font_icons import *
import theme.fonts.new_fonts as RRRFONT

def unlock_function(self):
    new_state = Qt.CheckState.Unchecked if self.bubbles_overlay.locked else Qt.CheckState.Checked
    self.bubbles_overlay.toggle_lock(new_state.value)




def r_dropdown(self, position):
    config = ContextMenuConfig()
    config.item_radius = 14
    config.font = RRRFONT.get_font(12)
    config.item_spacing = 29
    config.use_extended_shape = True
    config.auto_close = True
    config.close_on_outside = True

    ICON_LOCK_state = ICON_LOCK if self.bubbles_overlay.locked else ICON_LOCK_OPEN


    options_list = [
        ICON_LOCK_state,
        "?",
        ICON_MENU,
        ICON_POWER,
    ]

    config.toggle_values = {
            ICON_LOCK_state: not self.bubbles_overlay.locked,
    }

    config.callbackL = {
        ICON_LOCK_state:  lambda: (
                               unlock_function(self),
                               ctx.update_item(ICON_LOCK_state, "symbol", ICON_LOCK if self.bubbles_overlay.locked else ICON_LOCK_OPEN),
            ),
        ICON_POWER: lambda: QTimer.singleShot(500, self.close),
    }



    config.additional_texts = {
        ICON_LOCK_state: "Edit",
        "?": "Help",
        ICON_MENU: "Settings",
        ICON_POWER: "Exit",
    }



    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=self.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )