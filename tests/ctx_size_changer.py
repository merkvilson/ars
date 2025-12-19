from ui.widgets.context_menu import CtxConfig

config = CtxConfig()
config.custom_width = ars_window.width() 
config.options = {"1": "Slider 1",}
config.slider_values = {"1": (10,500,50)}

def update_geometry(value):    
    new_height = int(value)
    rect = ctx.geometry()
    # Calculate new Y position to keep the bottom fixed
    new_y = rect.y() + (rect.height() - new_height)
    ctx.move(rect.x(), new_y)
    ctx.setFixedSize(ars_window.width(), new_height)

config.callbackL={"1": update_geometry}
config.incremental_values={"1": 3}

ctx = config.open_context()