import json
from ui.widgets.context_menu import CtxConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.r_dropdown import r_dropdown
import os
import importlib
import inspect


def execute_cmd(ars_window):
    config = CtxConfig()
    config.dock_area = "top"
    config.auto_close = False
    config.close_on_outside = False
    config.use_extended_shape = False
    config.distribution_mode = "x"


    items = ["   ",]

    for filename in os.listdir(os.path.join('ars_cmds','bubble_cmds')):
        if filename.endswith(".py") and "__init__" not in filename:
            module_name = filename[:-3]
            module = importlib.import_module(f"ars_cmds.bubble_cmds.{module_name}")
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("BBL_"):
                    stem = name[4:]
                    config_var = name + "_CONFIG"
                    if hasattr(module, config_var):
                        config_dict = getattr(module, config_var)
                        if isinstance(config_dict, dict):
                            if not config_dict.get("visible", True):
                                continue
                            symbol = config_dict.get("symbol", stem)
                        else:
                            symbol = stem
                    else:
                        symbol = getattr(ic, f'ICON_{stem.upper()}', stem)
                    
                    # Get the full file path of the module
                    module_file_path = os.path.abspath(module.__file__)
                    
                    items.append(symbol)
                    config.callbackL[symbol] = lambda *args, f=func: f(ars_window)
                    config.callbackR[symbol] = lambda *args, p=module_file_path: r_dropdown(ars_window, code_path=p)
    
    items.append("   ")
    
    ctx = config.open_context(parent=ars_window.central_widget, items=items)



    def load_layout(path=os.path.join("saved_layouts", "ctx_layouts", "layout.json")):
        
        try:
            with open(path, 'r') as f:
                new_items = json.load(f)
            ctx.close()
            
            set_a = [
            item
            for x in ctx.items
            for item in (x if isinstance(x, (list, tuple)) else [x])
            ]

            set_b = [
            item
            for x in new_items
            for item in (x if isinstance(x, (list, tuple)) else [x])
            ]


            difference = [item for item in set_a if item not in set_b]
            if difference:
                # print(f"Difference items: {difference}")
                new_items.append(difference)

            def filter_nested(nested, correct):
                result = []
                for item in nested:
                    if isinstance(item, list):
                        filtered = filter_nested(item, correct)
                        if filtered:  # keep non-empty sublists
                            result.append(filtered)
                    elif item in correct:
                        result.append(item)
                return result
            new_items = filter_nested(new_items, set_a)

            open_context(ctx.config, ctx.parent(), new_items, animated=True)

        except Exception as e:
            print(f"Error loading layout: {e}")


    load_layout()
