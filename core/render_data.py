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
        self.base_workflow = None
        if default_workflow_path and os.path.exists(default_workflow_path):
            with open(default_workflow_path, 'r', encoding='utf-8') as f:
                self.workflow_template = json.load(f)
                self.base_workflow = json.loads(json.dumps(self.workflow_template))

    def set_workflow(self, workflow):
        if not os.path.exists(workflow):
            workflow = os.path.join("extensions", "comfyui", "workflow", f"{workflow}.json")
        if not os.path.exists(workflow):
            print(f"Workflow file '{workflow}' not found.")
            return
        with open(workflow, 'r', encoding='utf-8') as f:
            self.workflow_template = json.load(f)
            self.base_workflow = json.loads(json.dumps(self.workflow_template))
            self.workflow_name = os.path.splitext(os.path.basename(workflow))[0]
 
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

    def set_ud(self, key, value):
        if not self.base_workflow: return

        target_node_id = None
        for node_id, node in self.base_workflow.items():
            if node.get("class_type") == "Airen_UD" and node.get("_meta", {}).get("title") == key:
                target_node_id = node_id
                break
        
        if not target_node_id:
            print(f"Airen_UD node with title '{key}' not found.")
            return

        for node_id, node in self.base_workflow.items():
            inputs = node.get("inputs", {})
            for input_key, input_val in inputs.items():
                if isinstance(input_val, list) and len(input_val) == 2 and str(input_val[0]) == str(target_node_id):
                    self.workflow_template[node_id]["inputs"][input_key] = value

    
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
        try:
            req = request.Request("http://127.0.0.1:8188/prompt", data=data)
            request.urlopen(req)
        except Exception as e:
            print(f"Error sending render data: {e}")
