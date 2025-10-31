from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.load_object import selected_object



def main(self):
    
    if not selected_object(self):
        return
    else: obj = selected_object(self)
    
    print(f"Selected object: {obj.name}")




def execute_plugin(window):
    main(window)
