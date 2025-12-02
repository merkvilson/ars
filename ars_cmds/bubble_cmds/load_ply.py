from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtWidgets import QFileDialog


def BBL_L(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
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
