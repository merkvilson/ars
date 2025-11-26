from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import json
from PyQt6.QtWidgets import QFileDialog

def BBL_J(*args):
    run_ext(__file__)



def load_json_file(ars_window, file_path=None):
    if file_path is None:
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Json File",
            "",
            "Json Files (*.json)",
        )
    if file_path:
        ars_window.prefs.json_ud_path = file_path



def execute_cmd(ars_window):

    if not ars_window.prefs.json_ud_path:
        default_workflow_path = r"C:\Users\gmerk\Downloads\ARS\tests\json_read_data\tst2.json" #Temporal default path
        load_json_file(ars_window, default_workflow_path)

    with open(ars_window.prefs.json_ud_path, 'r', encoding='utf-8') as f: workflow_template = json.load(f)

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
