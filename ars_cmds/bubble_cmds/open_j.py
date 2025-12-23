from ui.widgets.context_menu import CtxConfig, close_all_open_context_menus
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QColor
from ars_cmds.render_cmds.generate_render import generate_render
from ars_cmds.bubble_cmds.render_video import BBL_VIDEO as open_render_video
from ars_cmds.bubble_cmds.comfyui_node_editor import BBL_comfyui_node_editor as open_comfyui_node_editor
def BBL_WORKFLOW(*args):
    run_ext(__file__)

def load_json_file(ars_window, file_path=None):
    if file_path is None:
        file_path, _ = QFileDialog.getOpenFileName(None,"Select Json File","","Json Files (*.json)",)
    if file_path:
        ars_window.prefs.json_ud_path = file_path


def open_workflow_prompt_editor(ars_window, file_path=None):
    ars_window.prefs.json_ud_path = file_path if file_path else ars_window.prefs.json_ud_path
    load_json_file(ars_window, ars_window.prefs.json_ud_path)
    
    close_all_open_context_menus()
    open_render_video(ars_window)


    config=CtxConfig()
    config.options = {}
    config.extra_distance = [99999,0]

    ars_window.render_manager.set_workflow(ars_window.prefs.json_ud_path)
    workflow_template = ars_window.render_manager.workflow_template

    # Check if there are any Airen nodes
    if not any(node.get("class_type", "").startswith("Airen_") for node in workflow_template.values()):
        ars_window.render_manager.propagate_custom_nodes()
        workflow_template = ars_window.render_manager.workflow_template

    airen_class_types = ["Airen_Gui_Data", "Airen_Gui_Prompt"]#["Airen_Int", "Airen_Float", "Airen_Bool", "Airen_Str"]

    # Check Workflow Type (Image/Video/3D/etc)
    for _, node in workflow_template.items():
        if node.get("class_type") == "Airen_Workflow_Type":
            inputs = node.get("inputs", {})
            ars_window.prefs.workflow_type = inputs.get("workflow_type", "Image")

    # Gather all GUI data nodes
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


    # Get Prompt Node values (There can be only one prompt node with two outputs - positive and negative)
    for _, node in workflow_template.items():
        if node.get("class_type") == "Airen_Gui_Prompt":
            inputs = node.get("inputs", {})
            ars_window.prefs.json_positive = inputs.get("positive", "")
            ars_window.prefs.json_negative = inputs.get("negative", "")


    # Set default values from "Default_Values" node
    for _, node in workflow_template.items():
        inputs = node.get("inputs", {})
        if inputs.get("ud_name") == "Default_Values":
            config.close_on_outside = inputs.get("close_on_outside", True)
            config.auto_close = inputs.get("auto_close", False)
            config.incremental_value = inputs.get("incremental_value", True)
            config.show_value = inputs.get("show_value", True)

            workflow_type = inputs.get("workflow_type", "Image")
            if workflow_type in ["Image", "Video", "Sprite"]:
                ars_window.viewport.hide()
                ars_window.img.show()
        else:
            config.close_on_outside = False
            config.auto_close = False
            config.incremental_value = True
            config.show_value = True
            ars_window.viewport.hide()
            ars_window.img.show()

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
        

        # We must update the render_manager's workflow_template directly because that is what generate_render uses.
        # The local 'workflow_template' variable is independent and changes to it won't affect the render.
        for _, node in ars_window.render_manager.workflow_template.items():
            if node.get("class_type") in airen_class_types:
                inputs = node.get("inputs", {})
                if inputs.get("ud_name") == 'prompt':
                    inputs["positive"] = ars_window.prefs.json_positive
                    inputs["negative"] = ars_window.prefs.json_negative

        generate_render(ars_window, ctx, int(ctx.get_value(ic.ICON_STEPS)), None)



    config.options = {ic.ICON_PLAYER_PLAY: "Run", **config.options}
    config.color[ic.ICON_PLAYER_PLAY] = QColor.fromRgbF(0.304, 0.471937, 0.8, 1.0)
    config.hover_color[ic.ICON_PLAYER_PLAY] = QColor.fromRgbF(0.3822,  0.657188, 0.98,  1.0)
    config.callbackL[ic.ICON_PLAYER_PLAY] = start_render
    
    ctx = config.open_context()


def execute_cmd(ars_window):
    open_workflow_prompt_editor(ars_window)
    open_comfyui_node_editor(ars_window)