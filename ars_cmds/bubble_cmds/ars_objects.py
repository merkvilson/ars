import os
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtGui import QCursor
from ars_cmds.core_cmds.load_object import (
    add_mesh,
    add_sprite,
    add_text3d,
    add_primitive,
)


BBL_OBJECT_CONFIG = {"symbol": ic.ICON_OBJ_BBOX, "hotkey": "G"}


def BBL_OBJECT(*args):
    run_ext(__file__)


def execute_plugin(ars_window):
    config = ContextMenuConfig()

    config.options = {
        ic.ICON_OBJ_TXT_ABC: 'Text',
        ic.ICON_OBJ_SPRITE: '2D Sprite',
        ic.ICON_OBJ_BOX: 'Cube',
        ic.ICON_OBJ_SPHERE: 'Sphere',
        ic.ICON_OBJ_CYLINDER: 'Cylinder',
        ic.ICON_OBJ_CONE: 'Cone',
        ic.ICON_OBJ_PYRAMID: 'Pyramid',
        ic.ICON_OBJ_PLANE: 'Plane',
        ic.ICON_OBJ_DISC: 'Disc',
        ic.ICON_OBJ_TORUS: 'Torus',
        ic.ICON_FILE_3D: 'Load Object',
        ic.ICON_ORIGAMI: 'Test Mesh',
    }

    config.callbackL = {
        ic.ICON_OBJ_TXT_ABC: lambda: add_text3d(),
        ic.ICON_OBJ_SPRITE: lambda: add_sprite(animated=True),
        ic.ICON_OBJ_BOX: lambda: add_primitive("cube", animated=True),
        ic.ICON_OBJ_SPHERE: lambda: add_primitive("sphere", animated=True),
        ic.ICON_OBJ_CYLINDER: lambda: add_primitive("cylinder", animated=True),
        ic.ICON_OBJ_CONE: lambda: add_primitive("cone", animated=True),
        ic.ICON_OBJ_PYRAMID: lambda: add_primitive("pyramid", animated=True),
        ic.ICON_OBJ_PLANE: lambda: add_primitive("plane", animated=True),
        ic.ICON_OBJ_DISC: lambda: add_primitive("disc", animated=True),
        ic.ICON_OBJ_TORUS: lambda: add_primitive("torus", radius_inner=0.25, animated=True),
        ic.ICON_ORIGAMI: lambda: add_mesh(os.path.join("res", "mesh files", "origami.obj"),animated=True,),
        ic.ICON_FILE_3D: lambda: add_mesh(),
    }

    config.hotkey_items = {
        ic.ICON_OBJ_TXT_ABC: "A",
        ic.ICON_OBJ_SPRITE: "2",
        ic.ICON_OBJ_BOX: "C",
        ic.ICON_OBJ_SPHERE: "S",
        ic.ICON_OBJ_CYLINDER: "L",
        ic.ICON_OBJ_CONE: "Q",
        ic.ICON_OBJ_PYRAMID: "Y",
        ic.ICON_OBJ_PLANE: "P",
        ic.ICON_OBJ_DISC: "D",
        ic.ICON_OBJ_TORUS: "T",
        ic.ICON_FILE_3D: "L",
        ic.ICON_ORIGAMI: "O",
    }

    ctx = open_context(config)
