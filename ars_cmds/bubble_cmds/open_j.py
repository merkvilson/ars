from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import json
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QColor
from ars_cmds.render_cmds.generate_render import generate_render

def BBL_WORKFLOW(*args):
    run_ext(__file__)

def load_json_file(ars_window, file_path=None):
    if file_path is None:
        file_path, _ = QFileDialog.getOpenFileName(None,"Select Json File","","Json Files (*.json)",)
    if file_path:
        ars_window.prefs.json_ud_path = file_path

def execute_cmd(ars_window):

    config=ContextMenuConfig()
    config.options = {}
    config.extra_distance = [99999,0]


    if not ars_window.prefs.json_ud_path:
        default_workflow_path = r"extensions\comfyui\test.json" #Temporal default path
        load_json_file(ars_window, default_workflow_path)

    ars_window.render_manager.set_workflow(ars_window.prefs.json_ud_path)

    with open(ars_window.prefs.json_ud_path, 'r', encoding='utf-8') as f: workflow_template = json.load(f)

    airen_class_types = ["Airen_Gui_Data"]#["Airen_Int", "Airen_Float", "Airen_Bool", "Airen_Str"]

    # First, gather all GUI data nodes
    for _, node in workflow_template.items():
        if node.get("class_type") in airen_class_types:
            inputs = node.get("inputs", {})
            if 'symbol' in inputs:
                gui_node_inputs = inputs

                symbol = getattr(ic, gui_node_inputs["symbol"])
                additional_text = gui_node_inputs.get("additional_text", "")
                slider_values = gui_node_inputs.get("slider_values", "0,100,1")
                config.options[symbol] = additional_text
                config.slider_values[symbol] = [float(x) for x in slider_values.split(",")]
                
    # Set default values from "Default_Values" node
    for _, node in workflow_template.items():
        inputs = node.get("inputs", {})
        if inputs.get("ud_name") == "Default_Values":
            config.close_on_outside = inputs.get("close_on_outside", True)
            config.auto_close = inputs.get("auto_close", False)
            config.incremental_value = inputs.get("incremental_value", True)
            config.show_value = inputs.get("show_value", True)

    def start_render():
        for _, node in workflow_template.items():
            if node.get("class_type") in airen_class_types:
                inputs = node.get("inputs", {})
                if 'symbol' in inputs and 'ud_name' in inputs:
                    symbol_name = inputs["symbol"]
                    if hasattr(ic, symbol_name):
                        symbol = getattr(ic, symbol_name)
                        value = ctx.get_value(symbol)
                        if value is not None:
                            ars_window.render_manager.set_userdata(inputs["ud_name"], value)
        
        #ars_window.render_manager.send_render()
            generate_render(ars_window, ctx, int(ctx.get_value(ic.ICON_STEPS)), None)




    config.options = {ic.ICON_PLAYER_PLAY: "Run", **config.options}
    config.color[ic.ICON_PLAYER_PLAY] = QColor.fromRgbF(0.304, 0.471937, 0.8, 1.0)
    config.hover_color[ic.ICON_PLAYER_PLAY] = QColor.fromRgbF(0.3822,  0.657188, 0.98,  1.0)
    config.callbackL[ic.ICON_PLAYER_PLAY] = start_render
    
    ctx = open_context(config)
