import os
from theme.fonts import font_icons as ic
from ars_cmds import bubble_cmds as Bcmd

imgs = (".png", ".jpg", ".jpeg", ".bmp")
objs = ('.obj','.stl','.ply','.off','.dae','.glb','.gltf','.3mf')
ars = (".arsp", ".arss",)

from .run_ext import run_ext

def dd_drag(self, event):

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

    else: ttip,sym = "Files", ic.ICON_FILES


    self.CF.UP("additional_text", ttip,  sym, False)

    if event.mimeData().hasUrls(): event.accept()
    else: event.ignore()


def dd_drop(self, event):
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



        else: ttip,sym = "", "?"


    self.CF.UP("additional_text", ttip, sym, True)