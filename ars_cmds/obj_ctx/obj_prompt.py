from ui.widgets.context_menu import ContextMenuConfig, open_context

from theme.fonts import font_icons as ic
from ui.widgets.multi_line_input import MultiLineInputWidget
from ars_cmds.mesh_gen.generate_sprite import generate_sprite
from ars_cmds.bubble_cmds.delete_selected_obj import BBL_TRASH as delete_obj

from PyQt6.QtGui import QCursor

from ars_cmds.util_cmds.delete_files import delete_all_files_in_folder
from ars_cmds.mesh_gen.generate_mesh import generate_mesh

from prefs.pref_controller import get_path
from PyQt6.QtCore import QPoint

import os


from PyQt6.QtGui import QColor

def prompt_ctx(self, position, default_object = None, callback = None):

    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
   # config.expand = "x"
    config.use_extended_shape = False
    config.distribution_mode = "x"
    config.anchor = "+y"
    config.custom_height = 260
    config.custom_width = 410

    config.extra_distance = [0,(config.item_radius * 2) - 6 ]


    if type(default_object).__name__ == "CSprite":
        self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "sprite.json")),



    options_list = [["T"],
    ["   ","A","   ",],

    [ic.ICON_STEPS, ic.ICON_GIZMO_SCALE,"   ", 
    ic.ICON_PLAYER_SKIP_BACK ,ic.ICON_PLAYER_PLAY, ic.ICON_PLAYER_SKIP_FORWARD, "   ", 
    ic.ICON_OBJ_HEXAGONS ,ic.ICON_SAVE], 

    ["   ",ic.ICON_CLOSE_RADIAL,"   "],
    ]

    config.slider_values = {
        ic.ICON_STEPS: (1, 50, default_object.steps),
        ic.ICON_GIZMO_SCALE: (25, 1024, 512),
        ic.ICON_CLOSE_RADIAL: (0,1,0),

    }

    def start_render(seed_step = 0):
        default_object.revert_cutout()

        delete_all_files_in_folder( get_path('steps') )
        default_object.seed += seed_step
        self.render_manager.set_userdata("seed", default_object.seed)
        self.render_manager.set_userdata("steps", int(ctx.get_value(ic.ICON_STEPS))),
        self.render_manager.set_userdata("positive", default_object.prompt)
        generate_sprite(self, ctx, max_steps=int(ctx.get_value(ic.ICON_STEPS)))

    def convert_sprite_to_mesh():
        delete_obj(self, position)
        generate_mesh(self, ctx)

    config.callbackL = {
        ic.ICON_PLAYER_PLAY: lambda: start_render(0),
        ic.ICON_PLAYER_SKIP_FORWARD: lambda: start_render(1),
        ic.ICON_PLAYER_SKIP_BACK: lambda: start_render(-1),
        ic.ICON_OBJ_HEXAGONS: lambda: convert_sprite_to_mesh(),
        ic.ICON_CLOSE_RADIAL: lambda: (ctx.close(), callback(self)),
        "T": lambda: print(prompt_widget.text_edit.toPlainText()),
    }

    config.callbackR = { ic.ICON_CLOSE_RADIAL: lambda value: ctx.move(  self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )
    }

    config.slider_color = {ic.ICON_CLOSE_RADIAL: QColor(150, 150, 150, 0)}


    def set_text_from_prompt():
        default_object.prompt = prompt_widget.text_edit.toPlainText()

    prompt_widget = MultiLineInputWidget()
    prompt_widget.text_edit.setPlainText(default_object.prompt)
    prompt_widget.text_edit.textChanged.connect(set_text_from_prompt)

    prompt_widget.setFixedSize(400, 140)

    config.custom_widget_items = {"A": prompt_widget}



    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
