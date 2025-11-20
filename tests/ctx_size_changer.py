from ui.widgets.context_menu import open_context, ContextMenuConfig
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QCursor
from util_functions.ars_window import ars_window

config = ContextMenuConfig()
main_win = ars_window
if callable(main_win):
    main_win = main_win()
config.custom_width = main_win.width() 
config.options = {
                "1": "Option 1",
                "2": "Option 2",
                "3": "Option 3",
                }
                
config.slider_values = {"1": (10,500,50)}

def update_geometry(value):
    if 'ctx' not in globals() or ctx is None: return
    
    # Get the main window instance properly
    main_win = ars_window
    if callable(main_win):
        main_win = main_win()
    if not main_win: return

    new_height = int(value)
    rect = ctx.geometry()
    
    # Calculate new Y position to keep the bottom fixed
    # new_y = current_y + (current_height - new_height)
    new_y = rect.y() + (rect.height() - new_height)
    
    ctx.move(rect.x(), new_y)
    ctx.setFixedSize(main_win.width(), new_height)

config.callbackL={"1": update_geometry}
config.incremental_values={"1": 3}

ctx = open_context(config)