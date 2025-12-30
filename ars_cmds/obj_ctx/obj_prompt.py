import os

from PyQt6.QtCore import QPoint, QTimer
from PyQt6.QtGui import QCursor

from ars_cmds.bubble_cmds.delete_selected_obj import BBL_TRASH as delete_obj
from ars_cmds.core_cmds.key_check import key_check_continuous
from ars_cmds.mesh_gen.generate_mesh import generate_mesh
from ars_cmds.render_cmds.check import check_queue_async
from ars_cmds.render_cmds.generate_render import generate_render
from ars_cmds.render_cmds.make_screenshot import make_screenshot
from ars_cmds.render_cmds.render_pass import save_depth, save_render
from ars_cmds.util_cmds.copy_to import copy_file_to_dir
from prefs.pref_controller import get_path
from theme.fonts import font_icons as ic
from ui.widgets.context_menu import CtxConfig
from ui.ars_code import PromptEditor

def prompt_ctx(self, position, default_object = None, callback = None):

    if not callback:
        def close_callback(arg=None):
            pass        
        callback = close_callback 

    config = CtxConfig()
    config.auto_close = False
    config.close_on_outside = False
    config.use_extended_shape = False
    config.distribution_mode = "x"
    config.anchor = "+y"
    config.custom_height = 260
    config.custom_width = 410
    config.extra_distance = [0,(config.item_radius * 2) - 6 ]
    config.incremental_value = True
    # config.close_duplicate = False
    # config.incremental_values = {ic.ICON_STEPS: 1, ic.ICON_GIZMO_SCALE: 1}



    options_list = [
    ["PromptEditorWidget"],

    [ic.ICON_STEPS, ic.ICON_GIZMO_SCALE,"   ", 
    ic.ICON_PLAYER_SKIP_BACK ,ic.ICON_PLAYER_PLAY, ic.ICON_PLAYER_SKIP_FORWARD, "   ", 
    ic.ICON_OBJ_HEXAGONS ,ic.ICON_SAVE], 

    ["   ",ic.ICON_CLOSE_RADIAL,"   "],
    ]

    config.slider_values = {
        ic.ICON_STEPS: (1, 50, default_object.steps),
        ic.ICON_GIZMO_SCALE: (25, 1024, 512),

    }


    def start_vp_img_render(seed_step = 0):
        def do_render():
            default_object.seed += seed_step

            if type(default_object).__name__ == "CSprite":
                default_object.revert_cutout()
                self.render_manager.set_workflow("sprite"),
            
            elif type(default_object).__name__ == "CPoint":
                self.render_manager.set_workflow("bg"),
                
            else:
                save_depth(self.viewport, x=int(ctx.get_value(ic.ICON_GIZMO_SCALE)), y=int(ctx.get_value(ic.ICON_GIZMO_SCALE)))
                save_render(self.viewport, x=int(ctx.get_value(ic.ICON_GIZMO_SCALE)), y=int(ctx.get_value(ic.ICON_GIZMO_SCALE)))
                self.render_manager.set_workflow("render"),

            self.render_manager.set_ud("seed", default_object.seed)
            self.render_manager.set_ud("steps", int(ctx.get_value(ic.ICON_STEPS)))
            self.render_manager.set_ud("positive", default_object.prompt)
            self.render_manager.set_ud("negative", "Low quality, blurry, deformed, bad anatomy") #TODO: make editable

            generate_render(self, ctx, int(ctx.get_value(ic.ICON_STEPS)), default_object)

        def on_queue_result(queue_remaining):
            if queue_remaining > 0:
                # print("Render queue is busy, cannot start a new render.")
                return
            do_render()

        check_queue_async(callback=on_queue_result)


    realtime_timer = QTimer()
    def realtime_tick():
        if getattr(self, 'prefs', None) and self.prefs.realtime_preview:
            start_vp_img_render(0)
    realtime_timer.timeout.connect(realtime_tick)
    realtime_timer.start(1000)


    def convert_sprite_to_mesh():
        delete_obj(self, position)
        generate_mesh(self, ctx)


    def save_output(name = self.render_manager.workflow_name):
        if name == "render":
            copy_file_to_dir(get_path('last_step'), get_path('keyframes'), "frame", True)
        # elif name == "mesh_image":
        #     copy_file_to_dir(get_path('last_step'), get_path('input'), "mesh", False)



    config.callbackL = {
        ic.ICON_PLAYER_PLAY: lambda: start_vp_img_render(0),
        ic.ICON_PLAYER_SKIP_FORWARD: lambda: start_vp_img_render(1),
        ic.ICON_PLAYER_SKIP_BACK: lambda: start_vp_img_render(-1),
        ic.ICON_OBJ_HEXAGONS: lambda: convert_sprite_to_mesh(),
        ic.ICON_SAVE: lambda: save_output("render"),
        ic.ICON_CLOSE_RADIAL: lambda: (realtime_timer.stop(), ctx.close(), callback(self)),
    }
    def move_ctx():ctx.move(self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )
    config.callbackR = { ic.ICON_CLOSE_RADIAL: lambda: key_check_continuous(callback=move_ctx, key='right', interval=4) }



    def set_text_from_prompt():
        default_object.prompt = editor.toPlainText()

    editor = PromptEditor()
    editor.setFixedSize(400, 140)
    editor.setPlainText(default_object.prompt)
    editor.textChanged.connect(set_text_from_prompt)

    config.custom_widget_items = {"PromptEditorWidget": editor}

    ctx = config.open_context(
        parent=self.central_widget,
        items=options_list,
        position=position
    )
