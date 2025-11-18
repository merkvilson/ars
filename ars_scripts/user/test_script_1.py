from ui.widgets.context_menu import open_context, ContextMenuConfig


config = ContextMenuConfig()
config.options = {
                "1": "Option 1",
                "2": "Option 2",
                "3": "Option 3",
                }
config.callbackL("1": lambda: add_primitive("sphere") ) 

open_context(config)