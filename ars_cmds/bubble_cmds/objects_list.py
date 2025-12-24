from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ui.widgets.hierarchy_tree import ObjectHierarchyWindow

from ars_cmds.bubble_cmds.delete_selected_obj import BBL_TRASH as delete_cmd
from ars_cmds.bubble_cmds.view_camera import view_selected

BBL_LIST_CONFIG ={"symbol": ic.ICON_LIST }
def BBL_LIST(*args):
    run_ext(__file__)


def execute_cmd(ars_window):
    hierarchy = ObjectHierarchyWindow(ars_window.viewport)

    # Integrate with SplitterOverlay
    if hasattr(ars_window, 'splitter_overlay'):
        overlay = ars_window.splitter_overlay
        
        # Set width
        width = getattr(ars_window.prefs, 'objects_list_width', 300)
        overlay.left_width = width
        
        overlay.set_widget("left", hierarchy)
        
        # Force update to apply width and layout
        overlay._update_mask()
        overlay._update_geometries()
        overlay.update()

