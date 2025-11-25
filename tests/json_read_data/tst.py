import os
import json

default_workflow_path = r"C:\Users\gmerk\Downloads\ARS\tests\json_read_data\tst.json"

with open(default_workflow_path, 'r', encoding='utf-8') as f: workflow_template = json.load(f)

airen_class_types = ["Airen_Int"]

test_dict = {}
def get_gui_data():
    for _, node in workflow_template.items():
        if node.get("class_type") in airen_class_types:
            inputs = node.get("inputs", {})
            if inputs.get("gui_expose") == True:
                print(f"Exposed Input: {inputs}")
                test_dict[inputs["ud_name"]] = inputs["ud_name"]

get_gui_data()
print(" ")
print(test_dict)