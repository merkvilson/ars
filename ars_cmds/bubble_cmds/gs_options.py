from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ui.widgets.context_menu import ContextMenuConfig, open_context, close_all_open_context_menus
from PyQt6.QtWidgets import QFileDialog


def BBL_ATOM(*args):
    run_ext(__file__)



def load_ply(ars_window):
    """Load a PLY file into the Gaussian Splatting viewer."""
    file_path, _ = QFileDialog.getOpenFileName(
        ars_window,
        "Select PLY File",
        "",
        "PLY Files (*.ply)",
    )
    if file_path:
        # Switch to gs_viewer if not already visible
        if not ars_window.gs_viewer.isVisible():
            ars_window.viewport.hide()
            ars_window.img.hide()
            ars_window.gs_viewer.show()
        
        count = ars_window.gs_viewer.load_ply(file_path)
        if count:
            ars_window.msg(f"Loaded {count} gaussians", auto_close=2000)
        else:
            ars_window.msg("Failed to load PLY file", auto_close=2000)

def auto_sort(ars_window):
    """Toggle auto-sort for Gaussian Splatting viewer."""
    gs = ars_window.gs_viewer
    new_state = not gs.auto_sort
    gs.set_auto_sort(new_state)
    
  
def execute_cmd(ars_window):

    config = ContextMenuConfig()
    config.auto_close = False
    config.options =  {
        ic.ICON_GRID_POINTS: "Auto-Sort",
        ic.ICON_FILE_3D: "Load PLY",
        ic.ICON_SHADER_SMOOTH: "Render Mode",
        ic.ICON_A_B_2: "Swap"}
    
    config.toggle_values = {ic.ICON_SHADER_SMOOTH: (0,7,0)}  # Render Mode options

    config.callbackL = {
        ic.ICON_GRID_POINTS: lambda: auto_sort(ars_window),
        ic.ICON_FILE_3D: lambda: load_ply(ars_window),
        ic.ICON_SHADER_SMOOTH: lambda mode: ars_window.gs_viewer.set_render_mode(mode),
        ic.ICON_A_B_2: lambda: ars_window.swap_widgets(),
    }

    ctx = open_context(config)