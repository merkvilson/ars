# core/render_data.py
import json
import os
from urllib import request
from PyQt6.QtCore import QObject

class RenderDataManager(QObject):
    """Manages render data settings, storage, and sending to backend."""
    
    def __init__(self, default_workflow_path=None):
        super().__init__()
        
        self.workflow_name = ""

        # Load default workflow JSON if provided (like your default.json)
        self.workflow_template = None
        if default_workflow_path and os.path.exists(default_workflow_path):
            with open(default_workflow_path, 'r', encoding='utf-8') as f:
                self.workflow_template = json.load(f)

    def set_workflow(self, workflow_json):
        with open(workflow_json, 'r', encoding='utf-8') as f:
            self.workflow_template = json.load(f)
            self.workflow_name = os.path.splitext(os.path.basename(workflow_json))[0]
 
    def set_userdata(self, key, value):
        for _, node in self.workflow_template.items():
            inputs = node.get("inputs", {})
            if inputs.get("ud_name") == key:
                inputs["output"] = value
                return

        print(f"Userdata node with ud_name '{key}' not found.")


    def get_userdata(self, key):
        for _, node in self.workflow_template.items():
            inputs = node.get("inputs", {})
            if inputs.get("ud_name") == key:
                return inputs["output"]

        print(f"Userdata node with ud_name '{key}' not found.")

    
    def get_weights(self):
        weights = {}
        for _, node in self.workflow_template.items():
            inputs = node.get("inputs", {})
            if "weight" in inputs:
                weights[inputs["output"][0]]= inputs["weight"]

        sum_values = sum(weights.values())
        percentage_values = {k: (v / sum_values) * 100 for k, v in weights.items()}

        return percentage_values


    def send_render(self):
        if self.workflow_template is None: return

        data = json.dumps({"prompt": self.workflow_template}).encode('utf-8')
        req = request.Request("http://127.0.0.1:8188/prompt", data=data)
        request.urlopen(req)
