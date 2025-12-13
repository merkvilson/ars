import os
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from ars_cmds.core_cmds.cursor_to_xyz import get_xyz
from ars_cmds.core_cmds.key_check import key_check_continuous, key_check
from ars_cmds.util_cmds.time_cmd import after, delay
from core.cursor_modifier import set_cursor
from ars_cmds.core_cmds.load_object import (
    add_mesh,
    add_sprite,
    add_text3d,
    add_primitive,
    add_point,
)
from core.sound_manager import play_sound


BBL_OBJECT_CONFIG = {"symbol": ic.ICON_OBJ_BBOX, "hotkey": "G"}

def BBL_OBJECT(*args):
    run_ext(__file__)

def execute_cmd(ars_window):
    config = ContextMenuConfig()
    

    config.options = {
        ic.ICON_OBJ_TXT_ABC: 'Text',
        ic.ICON_OBJ_SPRITE: '2D Sprite',
        ic.ICON_OBJ_CUBE: 'Cube',
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
        ic.ICON_OBJ_SPRITE: lambda: add_sprite(animated=True, position=p),
        ic.ICON_OBJ_CUBE: lambda: add_primitive("cube", animated=True, position=p),
        ic.ICON_OBJ_SPHERE: lambda: add_primitive("sphere", animated=True, position=p),
        ic.ICON_OBJ_CYLINDER: lambda: add_primitive("cylinder", animated=True, position=p),
        ic.ICON_OBJ_CONE: lambda: add_primitive("cone", animated=True, position=p),
        ic.ICON_OBJ_PYRAMID: lambda: add_primitive("pyramid", animated=True, position=p),
        ic.ICON_OBJ_PLANE: lambda: add_primitive("plane", animated=True, position=p),
        ic.ICON_OBJ_DISC: lambda: add_primitive("disc", animated=True, position=p),
        ic.ICON_OBJ_TORUS: lambda: add_primitive("torus", radius_inner=0.25, animated=True, position=p),
        ic.ICON_ORIGAMI: lambda: add_mesh(os.path.join("res", "mesh files", "origami.obj"), animated=True, position=p),
        ic.ICON_FILE_3D: lambda: add_mesh(position=p),
    }


    config.hotkey_items = {
        ic.ICON_OBJ_TXT_ABC: "A",
        ic.ICON_OBJ_SPRITE: "2",
        ic.ICON_OBJ_CUBE: "C",
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

    if not key_check("G"):
        open_context(config)
        return

    p = (0, 0, 0)

    def new_p():
        nonlocal p
        ars_window.viewport.controller.set_handles([""])
        p = get_xyz(ars_window, [point])
        if p is None:
          p = (0, 0, 0)
        return p[0],p[1],p[2]

    point=add_primitive('sphere', animated=False, )
    point.set_scale(0.1)
    point.set_color((1,1,1,0.3))
    point.set_shading(None)

    primitive_objs = [None, "cube", "plane", "cylinder", "cone", "disc", "sphere", "torus", "pyramid"]
    select = primitive_objs[ars_window.prefs.last_sel_obj_id % len(primitive_objs)]

    def start():
        nonlocal select
        set_cursor("point", "bottom")
        ars_window.hotkey_manager._unbind_all()
        # Initialize with previously selected object
        if select:
            point.set_primitive_type(select)
            point.set_scale(0.45)
            if select == "torus":
                point.set_primitive_type("torus", radius_inner=0.25)
            elif select == "cylinder":
                point.set_color((0.5,0.5,0.5,1))
            else:
                point.set_color((1,1,1,0.4))
            ars_window.CF.UP(key="additional_text", value=select.capitalize(), auto_close = 2500, symbol=getattr(ic, "ICON_OBJ_"+select.upper()))

    def during():
        point.set_position(new_p()[0],new_p()[1]+0.45,new_p()[2])
        
    
    def end():
        set_cursor("cursor")
        point.remove()
        if select is None:
            open_context(config)
        else:
            primitive = add_primitive(select, animated=True, position=p)
            ars_window.CF.UP(key="additional_text", value=select.capitalize()+" Added", auto_close = 500, symbol=getattr(ic, "ICON_OBJ_"+select.upper()))
            if select == "torus":
                primitive.set_primitive_type("torus", radius_inner=0.25)        
        after(500, lambda: ars_window.hotkey_manager._bind_shortcuts())

        


    def scroll(value):
        nonlocal select
        play_sound("click")
        ars_window.prefs.last_sel_obj_id += value
        select = primitive_objs[ars_window.prefs.last_sel_obj_id % len(primitive_objs)]
        if select:
            point.set_primitive_type(select)
            point.set_scale(0.45)

            if select == "torus":
                point.set_primitive_type("torus", radius_inner=0.25)
            elif select == "cylinder":
                point.set_color((0.5,0.5,0.5,1))
            else:
                point.set_color((1,1,1,0.4))
            ars_window.CF.UP(key="additional_text", value=select.capitalize(), auto_close = 2500, symbol=getattr(ic, "ICON_OBJ_"+select.upper()))
        else:
            point.set_primitive_type("sphere")
            point.set_scale(0.1)
            ars_window.CF.UP(key="additional_text", value="Select Object", auto_close = 2500,symbol=ic.ICON_OBJ_BBOX)


    key_check_continuous(callback=during,
                         key="G",
                         interval=16,
                         callback_start=start,
                         callback_end=end,
                         scroll_callback=scroll
                         )
