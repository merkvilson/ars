from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext


def BBL_G(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    """Switch between viewport, img viewer, and gs_viewer."""
    ars_window.swap_widgets()
