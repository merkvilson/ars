from ui.widgets.context_menu import open_context, ContextMenuConfig

config = ContextMenuConfig()
config.custom_width = ars_window.width() 
config.options = {"1": "1", "2": "2", "3": "3", "4": "4"}

config.slider_values = {"1": (50,500,50), "2": (50,500,50), "3": (50,500,50), "4": (50,500,50)}


config.callbackL={"1": lambda value: ctx.resize_top(value)}
config.incremental_value= (-10,"y")

ctx = open_context(config)