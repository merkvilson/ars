from ars_cmds.core_cmds.key_check import key_check_continuous
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object
from PyQt6.QtCore import QPoint, QTimer


def BBL_2(self, position):
    run_ext(__file__, self)


def main(self, position):
    config = ContextMenuConfig()
    config.show_value = True

    config.slider_values = {
        "1": (0, 100, 50),
        "2": (0, 100, 50),

    }
    config.auto_close = False
    config.incremental_values = {
        "1": 1,
    }

    options_list = [
        ["1", "2"],
    ]
 

    config.additional_texts = {
    "1": "Slider INCR",
    "2": "Slider FREE",
    }


    config.callbackL = {
        "1": lambda value: print(value),
        "2": lambda value: print(value),
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )


def execute_plugin(window):
    main(window, position=window.central_widget.mapFromGlobal(QCursor.pos()))
