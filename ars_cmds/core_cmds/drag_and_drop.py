"""
Handles drag and drop functionality for the application.

This module defines functions to handle drag enter/move events and drop events,
processing various file types such as images, 3D objects, layouts, and scripts.
"""
import os
from theme.fonts import font_icons as ic
from ars_cmds import bubble_cmds as Bcmd

imgs = (".png", ".jpg", ".jpeg", ".bmp")
objs = ('.obj','.stl','.ply','.off','.dae','.glb','.gltf','.3mf')
ars = (".arsp", ".arss",)
jsons = (".json",) #TODO; implement

from .run_ext import run_ext

def dd_drag(self, event):
    """
    Handles the drag enter and drag move events.

    Updates the UI feedback (cursor/tooltip) based on the type of files being dragged.

    Args:
        self: The instance of the class calling this method (likely a window or widget).
        event: The drag event object containing mime data and URLs.
    """

    files = [u.toLocalFile() for u in event.mimeData().urls()]
    
    if not files:
        event.ignore()
        return
    
    first_file = os.path.basename(files[0])
    count = len(files)
    one = count == 1

    if all(s.endswith(imgs) for s in files):
        sym = ic.ICON_IMAGE
        ttip = first_file if one else f"{count} Images"

    elif all(s.endswith(objs) for s in files):
        sym = ic.ICON_FILE_3D
        ttip = first_file if one else f"{count} Objects"

    elif all(s.endswith(".arsl") for s in files):
        sym = ic.ICON_LAYOUT
        ttip = first_file if one else f"{count} Layouts"

    elif all(s.endswith(ars) for s in files):
        sym = ic.ICON_CODE_PYTHON
        ttip = first_file if one else f"{count} Scripts"

    elif all(s.endswith(jsons) for s in files):
        sym = ic.ICON_CODE_PYTHON #TODO; change icon
        ttip = first_file if one else f"{count} JSON Files"

    else: ttip,sym = "Files", ic.ICON_FILES


    self.CF.UP("additional_text", ttip,  sym, False, 255)

    if event.mimeData().hasUrls(): event.accept()
    else: event.ignore()


def dd_drop(self, event):
    """
    Handles the drop event.

    Processes the dropped files based on their extensions:
    - 3D Objects (.obj, .stl, etc.): Adds the mesh to the scene.
    - Images (.png, .jpg, etc.): Loads as background image.
    - Layouts (.arsl): Loads the UI layout.
    - Scripts (.py, .arsp): Runs the script.

    Args:
        self: The instance of the class calling this method.
        event: The drop event object containing mime data and URLs.
    """
    files = [u.toLocalFile() for u in event.mimeData().urls()]
    for f in files:

        if f.endswith(objs):
            Bcmd.add_mesh(f, True)
            ttip, sym = "Object Loaded!", ic.ICON_FILE_CHECK

        elif f.endswith(imgs):
            Bcmd.load_bg_image(self,f)
            ttip, sym = "Image Loaded!", ic.ICON_FILE_CHECK

        elif f.endswith(".arsl"):
            self.bubbles_overlay.load_layout(f)
            ttip, sym = "Layout Loaded!", ic.ICON_FILE_CHECK
    
        elif f.endswith(".py"):
            run_ext(f)
            ttip, sym = "Script Loaded!", ic.ICON_FILE_CHECK

    
        elif f.endswith(".arsp"):
            run_ext(f)
            ttip, sym = "Script Loaded!", ic.ICON_FILE_CHECK

        
        elif f.endswith(".json"):
            ttip, sym = "Load Json File", ic.ICON_CODE_PYTHON #TODO; implement
            from ars_cmds.bubble_cmds.open_j import open_workflow_prompt_editor
            open_workflow_prompt_editor(self)



        else: ttip,sym = "", "?"


    self.CF.UP("additional_text", ttip, sym, True)