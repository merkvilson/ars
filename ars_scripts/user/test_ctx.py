from ui.widgets.context_menu import open_context, ContextMenuConfig
from theme.fonts import font_icons as ic
import os
import json

default_workflow_path = r"C:\Users\gmerk\Downloads\ARS\tests\json_read_data\tst.json"

with open(default_workflow_path, 'r', encoding='utf-8') as f: workflow_template = json.load(f)

airen_class_types = ["Airen_Int"]

test_dict = {}
def get_gui_data(config):
    for _, node in workflow_template.items():
        if node.get("class_type") in airen_class_types:
            inputs = node.get("inputs", {})
            if inputs.get("gui_expose"):
                gui_node_id = inputs["gui_expose"][0]
                gui_node_inputs = workflow_template.get(gui_node_id).get("inputs")
                config.options[ getattr(ic, gui_node_inputs["symbol"]) ] =   gui_node_inputs["additional_text"]
                config.slider_values[getattr(ic, gui_node_inputs["symbol"])] =  [float(x) for x in gui_node_inputs["slider_values"].split(",")]


config=ContextMenuConfig()
config.options = {}
get_gui_data(config)

open_context(config)
