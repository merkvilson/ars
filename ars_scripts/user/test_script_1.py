from ui.widgets.context_menu import open_context, ContextMenuConfig

config=ContextMenuConfig()
config.options = {
                ic.ICON_OBJ_BOX:"Cube", 
                ic.ICON_OBJ_SPHERE:"Sphere", 
                ic.ICON_OBJ_PYRAMID:"Pyramid",
                }
config.callbackL = {
                ic.ICON_OBJ_BOX:lambda: add_primitive("cube"), 
                ic.ICON_OBJ_SPHERE:lambda: add_primitive("sphere"), 
                ic.ICON_OBJ_PYRAMID:lambda: add_primitive("pyramid"),
                }
open_context(config)
