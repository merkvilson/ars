from ui.widgets.context_menu import open_context, ContextMenuConfig

config=ContextMenuConfig()
config.auto_close=False
config.options = {
                ic.ICON_OBJ_PYRAMID:"Cube", 
                ic.ICON_OBJ_SPHERE:"Sphere", 
                ic.ICON_CIRCLE_DOWN:"Pyramid",
                }
open_context(config)
