from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor


import requests
ckpt_list = []
try:
    response = requests.get("http://127.0.0.1:8188/system_stats", timeout=0.1)
    if response.status_code == 200:

        url = "http://127.0.0.1:8188/object_info"
        response = requests.get(url)
        data = response.json()

        checkpoints = data['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]

        ckpt_list=checkpoints
        
except:
    print("Could not fetch ckpt list from ARS backend.")


BBL_CKPTLIST_CONFIG={"symbol": ic.ICON_BRAIN}
def BBL_CKPTLIST(*args):
    run_ext(__file__)

def execute_plugin(ars_window):
    config = ContextMenuConfig()
    config.auto_close = False
    config.item_radius = 15

    config.show_symbol = False
    def set_ckpt(ckpt_name):
        ars_window.render_manager.set_userdata("ckpt_name", ckpt_name)

    ckpt_index_list = [str(i + 1) for i in range(len(ckpt_list))]

    config.additional_texts = {str(i + 1): obj[:-len(".safetensors")] for i, obj in enumerate(ckpt_list)}

    config.callbackL = {str(i + 1): lambda x=obj: set_ckpt(x) for i, obj in enumerate(ckpt_list)} 

    print(ars_window.render_manager.get_userdata("ckpt_name"))

    #config.toggle_values = {str(i + 1): (0, 1, 0) for i in range(len(ckpt_list))}  
    
    #config.toggle_groups = [ckpt_index_list]

    ctx = open_context(
        parent=ars_window.central_widget,
        items=ckpt_index_list,
        position=ars_window.central_widget.mapFromGlobal(QCursor.pos()),
        config=config
    )

