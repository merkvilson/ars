# core/render_data.py
import json
import os
from urllib import request
from PyQt6.QtCore import QObject, pyqtSignal

class RenderDataManager(QObject):
    """Manages render data settings, storage, and sending to backend."""
    
    data_changed = pyqtSignal(dict)  # Emitted when settings update (for UI refresh)
    render_started = pyqtSignal()    # Emitted when send_render is called
    render_error = pyqtSignal(str)   # Emitted on errors

    def __init__(self, default_workflow_path=None):
        super().__init__()
        
        # Load default workflow JSON if provided (like your default.json)
        self.workflow_template = None
        if default_workflow_path and os.path.exists(default_workflow_path):
            with open(default_workflow_path, 'r') as f:
                self.workflow_template = json.load(f)



    def set_userdata(self, key, value):
        for node_id, node in self.workflow_template.items():
            inputs = node.get("inputs", {})
            if inputs.get("ud_name") == key:
                inputs["output"] = value
                return

        raise ValueError(f"Userdata node with ud_name '{key}' not found.")


    def get_userdata(self, key):
        for node_id, node in self.workflow_template.items():
            inputs = node.get("inputs", {})
            if inputs.get("ud_name") == key:
                return inputs["output"]

        raise ValueError(f"Userdata node with ud_name '{key}' not found.")



    def send_render(self):
        if self.workflow_template is None:
            return

        data = json.dumps({"prompt": self.workflow_template}).encode('utf-8')
        req = request.Request("http://127.0.0.1:8188/prompt", data=data)
        request.urlopen(req)
        self.render_started.emit()
