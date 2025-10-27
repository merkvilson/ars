import os
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic

from ..core_cmds.load_object import add_mesh, add_sprite

BBL_OBJECT_CONFIG = {"symbol": ic.ICON_OBJ_BBOX, "hotkey": "G"}
def BBL_OBJECT(self, position):
    config = ContextMenuConfig()

    options_list =  [
                    ic.ICON_SPRITE,
                     ic.ICON_OBJ_BOX,
                     ic.ICON_OBJ_SPHERE,
                     ic.ICON_OBJ_CYLINDER,
                     ic.ICON_OBJ_CONE,
                     ic.ICON_OBJ_PYRAMID,
                     ic.ICON_OBJ_PLANE,
                     ic.ICON_OBJ_TORUS,
                     ic.ICON_ORIGAMI,
                     ic.ICON_FILE_3D,
                     ]

    config.callbackL = {
        ic.ICON_SPRITE:            lambda: add_sprite(self),
        ic.ICON_OBJ_BOX:           lambda: add_mesh(self, os.path.join("res","mesh files", 'box.obj'      ), animated = True),
        ic.ICON_OBJ_SPHERE:        lambda: add_mesh(self, os.path.join("res","mesh files", 'sphere.obj'   ), animated = True),
        ic.ICON_OBJ_CYLINDER:      lambda: add_mesh(self, os.path.join("res","mesh files", 'cylinder.obj' ), animated = True),
        ic.ICON_OBJ_CONE:          lambda: add_mesh(self, os.path.join("res","mesh files", 'cone.obj'     ), animated = True),
        ic.ICON_OBJ_PYRAMID:       lambda: add_mesh(self, os.path.join("res","mesh files", 'pyramid.obj'  ), animated = True),
        ic.ICON_OBJ_PLANE:         lambda: add_mesh(self, os.path.join("res","mesh files", 'plane.obj'    ), animated = True),
        ic.ICON_OBJ_TORUS:         lambda: add_mesh(self, os.path.join("res","mesh files", 'torus.obj'    ), animated = True),
        ic.ICON_ORIGAMI:           lambda: add_mesh(self, os.path.join("res","mesh files", "origami.obj"  ), animated = True),
        ic.ICON_FILE_3D:           lambda: add_mesh(self),
    }

    config.additional_texts = {
        ic.ICON_SPRITE: '2D Sprite',
        ic.ICON_OBJ_BOX:   'Cube', 
        ic.ICON_OBJ_SPHERE: 'Sphere', 
        ic.ICON_OBJ_CYLINDER: 'Cylinder',
        ic.ICON_OBJ_CONE:   'Cone',
        ic.ICON_OBJ_PYRAMID: 'Pyramid',
        ic.ICON_OBJ_PLANE: 'Plane',
        ic.ICON_OBJ_TORUS: 'Torus',
        ic.ICON_FILE_3D: 'Import Object',
        ic.ICON_ORIGAMI: 'Test Mesh',
    }

    config.hotkey_items = {
        ic.ICON_SPRITE: 'D',
        ic.ICON_OBJ_BOX:    'C', 
        ic.ICON_OBJ_SPHERE:  'S', 
        ic.ICON_OBJ_CYLINDER: 'L',
        ic.ICON_OBJ_CONE:    'Q',
        ic.ICON_OBJ_PYRAMID: 'Y',
        ic.ICON_OBJ_PLANE: 'P',
        ic.ICON_OBJ_TORUS: 'T',
        ic.ICON_FILE_3D:  'I',
        ic.ICON_ORIGAMI:  'O',

    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
