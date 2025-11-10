from ars_cmds.core_cmds.key_check import key_check_continuous
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ui.widgets.multi_line_input import MultiLineInputWidget
from ars_cmds.bubble_cmds.delete_selected_obj import BBL_TRASH as delete_obj
from PyQt6.QtGui import QCursor
from ars_cmds.util_cmds.delete_files import delete_all_files_in_folder
from ars_cmds.mesh_gen.generate_mesh import generate_mesh
from prefs.pref_controller import get_path
from PyQt6.QtCore import QPoint
import os
from PyQt6.QtGui import QColor
from ars_cmds.core_cmds.load_object import selected_object
from ars_cmds.render_cmds.generate_render import generate_render
from ars_cmds.render_cmds.render_pass import save_depth, save_render
from ars_cmds.render_cmds.check import check_queue
from ars_cmds.util_cmds.copy_to import copy_file_to_dir
from ars_cmds.render_cmds.make_screenshot import make_screenshot

def prompt_ctx(self, position, default_object = None, callback = None):

    if not callback:
        def close_callback(arg=None):
            pass        
        callback = close_callback 

    print("Opening prompt context menu")

    config = ContextMenuConfig()
    config.auto_close = False
    config.close_on_outside = False
    config.use_extended_shape = False
    config.distribution_mode = "x"
    config.anchor = "+y"
    config.custom_height = 260 + (300 if default_object == self else 0)
    config.custom_width = 450
    config.extra_distance = [0,(config.item_radius * 2) - 6 ]



    options_list = [
    ["   ","prompt_widget","   ",],

    [ic.ICON_STEPS, ic.ICON_GIZMO_SCALE,"   ", 
    ic.ICON_PLAYER_SKIP_BACK ,ic.ICON_PLAYER_PLAY, ic.ICON_PLAYER_SKIP_FORWARD, "   ", 
    ic.ICON_OBJ_HEXAGONS ,ic.ICON_SAVE], 

    ["   ",ic.ICON_CLOSE_RADIAL,"   "],
    ]

    if default_object == self: options_list.insert(0, [ic.ICON_IMAGE])
    config.image_items = {ic.ICON_IMAGE: r" "}
    config.use_extended_shape_items = {ic.ICON_IMAGE: (9.5, 6)}
    config.per_item_radius = { ic.ICON_IMAGE: 23,}

    config.slider_values = {
        ic.ICON_STEPS: (1, 50, default_object.steps),
        ic.ICON_GIZMO_SCALE: (25, 1024, 512),
       # ic.ICON_CLOSE_RADIAL: (0,1,0),

    }

    def start_render(seed_step = 0):
        if check_queue(): 
            print("Render queue is busy, cannot start a new render.")
            return
    
        default_object.seed += seed_step



        if type(default_object).__name__ == "CSprite":
            default_object.revert_cutout()
            self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "sprite.json")),
        
        elif type(default_object).__name__ == "CPoint":
            self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "bg.json")),
            
        else:
            save_depth(self.viewport, x=int(ctx.get_value(ic.ICON_GIZMO_SCALE)), y=int(ctx.get_value(ic.ICON_GIZMO_SCALE)))
            save_render(self.viewport, x=int(ctx.get_value(ic.ICON_GIZMO_SCALE)), y=int(ctx.get_value(ic.ICON_GIZMO_SCALE)))
            self.render_manager.set_workflow(os.path.join("extensions","comfyui","workflow", "render.json")),

        self.render_manager.set_userdata("seed", default_object.seed)
        self.render_manager.set_userdata("steps", int(ctx.get_value(ic.ICON_STEPS))),
        self.render_manager.set_userdata("positive", default_object.prompt)

        delete_all_files_in_folder( get_path('steps') )

        generate_render(self, ctx, int(ctx.get_value(ic.ICON_STEPS)), default_object)


    def convert_sprite_to_mesh():
        delete_obj(self, position)
        generate_mesh(self, ctx)


    def save_output(name = self.render_manager.workflow_name):
        if name == "mesh_image":
            copy_file_to_dir(get_path('last_step'), get_path('input'), "mesh", False)
        elif name == "render":
            copy_file_to_dir(get_path('last_step'), get_path('keyframes'), "frame", True)


    def swap_imge(self):
        image_path = os.path.join(get_path('input'), "vp_screenshot.png")       
        if self.viewport.isVisible():
            def post_screenshot():
                ctx.update_item(ic.ICON_IMAGE, "image_path", image_path)
                files = os.listdir(get_path('steps')) 
                full_paths = [os.path.join(get_path('steps'), f) for f in files]
                if full_paths:
                    latest_file = max(full_paths, key=os.path.getmtime)
                    if hasattr(self, 'img') and self.img:
                        self.img.open_image(latest_file)
                self.swap_widgets()
                if full_paths: self.img.fit_image()
            make_screenshot(self, callback=post_screenshot, x=200, y=200, name="vp_screenshot.png")
        else:
            self.swap_widgets()
            #if not self.viewport.isVisible() and hasattr(self, 'img') and self.img and get_path('last_step'):
               # self.img.open_image(get_path('last_step'))



    config.callbackL = {
        ic.ICON_PLAYER_PLAY: lambda: start_render(0),
        ic.ICON_PLAYER_SKIP_FORWARD: lambda: start_render(1),
        ic.ICON_PLAYER_SKIP_BACK: lambda: start_render(-1),
        ic.ICON_OBJ_HEXAGONS: lambda: convert_sprite_to_mesh(),
        ic.ICON_SAVE: lambda: save_output("render"),
        ic.ICON_CLOSE_RADIAL: lambda: (ctx.close(), callback(self)),
        ic.ICON_IMAGE: lambda: swap_imge(self),

    }
    def move_ctx():
        ctx.move(  self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )
    config.callbackR = { ic.ICON_CLOSE_RADIAL: lambda: key_check_continuous(callback=move_ctx, key='r', interval=4) }

    config.slider_color = {ic.ICON_CLOSE_RADIAL: QColor(150, 150, 150, 0)}


    def set_text_from_prompt():
        default_object.prompt = prompt_widget.text_edit.toPlainText()

    prompt_widget = MultiLineInputWidget()
    prompt_widget.text_edit.setPlainText(default_object.prompt)
    prompt_widget.text_edit.textChanged.connect(set_text_from_prompt)

    prompt_widget.setFixedSize(440, 140)

    config.custom_widget_items = {"prompt_widget": prompt_widget}



    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
