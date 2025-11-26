import os
import json

default_workflow_path = r"C:\Users\gmerk\Downloads\ARS\tests\json_read_data\test2.json"

with open(default_workflow_path, 'r', encoding='utf-8') as f: workflow_template = json.load(f)

def get_gui_data():
    for _, node in workflow_template.items():
        if node.get("class_type") in ["Airen_Gui_Data"]:
            inputs = node.get("inputs", {})
            if 'ud_name' in inputs:
                print(inputs)

get_gui_data()

# print(workflow_template)
