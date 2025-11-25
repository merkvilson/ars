import os
import json

default_workflow_path = r"C:\Users\gmerk\Downloads\ARS\tests\json_read_data\tst.json"

with open(default_workflow_path, 'r', encoding='utf-8') as f: workflow_template = json.load(f)

airen_class_types = ["Airen_Int"]

test_dict = {}
def get_gui_data():
    for node_id, node in workflow_template.items():
        if node.get("class_type") in airen_class_types:
            inputs = node.get("inputs", {})
            if inputs.get("gui_expose"):
                gui_node_id = inputs["gui_expose"][0]
                gui_node_inputs = workflow_template.get(gui_node_id).get("inputs")
                print(gui_node_inputs)

get_gui_data()
