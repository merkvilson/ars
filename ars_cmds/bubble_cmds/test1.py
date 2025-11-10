from ars_cmds.core_cmds.key_check import key_check
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import selected_object
from PyQt6.QtCore import QPoint, QTimer


BBL_TEST_CONFIG ={"symbol": ic.ICON_TEST }
def BBL_TEST(self, position):
    run_ext(__file__, self)


def main(self, position):
    config = ContextMenuConfig()


    options_list = [
        ["1", "2"],
    ]
 

    config.additional_texts = {
    "1": "Button 1",
    "2": "Button 2",
    }

    check_timer = None

    def on_button_1_pressed():
        nonlocal check_timer
        print("Button 1 was pressed!")
        
        # Stop any existing timer
        if check_timer is not None:
            check_timer.stop()
            check_timer.deleteLater()
        
        # Create a new timer to check key state
        check_timer = QTimer()
        
        def check_key_state():
            if key_check("left"):
                print("Left mouse button is being held down!")
            else:
                # Stop timer when key is released
                print("Left mouse button released.")
                check_timer.stop()
                check_timer.deleteLater()
        
        check_timer.timeout.connect(check_key_state)
        check_timer.start(100)  # Check every 100 milliseconds
        
        # Also execute once immediately
        check_key_state()

    config.callbackL = {
        "1": lambda: on_button_1_pressed(),
        "2": lambda: print("Button 2 pressed"),
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )


def execute_plugin(window):
    main(window, position=window.central_widget.mapFromGlobal(QCursor.pos()))
