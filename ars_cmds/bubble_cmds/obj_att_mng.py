from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from PyQt6.QtGui import QCursor, QColor
from ars_cmds.core_cmds.key_check import key_check_continuous

from ars_cmds.obj_ctx.obj_color_ctx import obj_color
from ars_cmds.obj_ctx.obj_psr import obj_scale
from ars_cmds.obj_ctx.obj_prompt import prompt_ctx
from ars_cmds.obj_ctx.obj_primitive_ctx import obj_primitive_ctx

from ars_cmds.bubble_cmds.delete_selected_obj import BBL_TRASH  as delete_selected_obj
from PyQt6.QtCore import QPoint


def obj_att_mng(self, ):

    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return

    mouse_pos = self.central_widget.mapFromGlobal(QCursor.pos())
    config = ContextMenuConfig()
    #config.close_on_outside = False
    #config.auto_close = False
    config.distribution_mode = "radial"
    config.use_extended_shape = False
    config.background_color = (255, 255, 255, 0)
    config.set_arc_range(-180,0)


    
    options_list = [ic.ICON_CLOSE_RADIAL, ic.ICON_PALETTE, ic.ICON_SETTINGS, ic.ICON_GIZMO_SCALE_3D, ic.ICON_LOCK, ic.ICON_TRASH, ic.ICON_TEXT_INPUT, ]

    config.callbackL = {ic.ICON_PALETTE:        lambda: (obj_color(self,mouse_pos, obj_att_mng),                ctx.close()),
                        ic.ICON_SETTINGS:       lambda: (obj_primitive_ctx(self, mouse_pos, obj_att_mng),       ctx.close()),
                        ic.ICON_GIZMO_SCALE_3D: lambda: (obj_scale(self,mouse_pos, obj_att_mng),                ctx.close()),
                        ic.ICON_TRASH:          lambda: (delete_selected_obj(self, None),                       ctx.close()),
                        ic.ICON_TEXT_INPUT:     lambda: (prompt_ctx(self, mouse_pos, selected[0], obj_att_mng), ctx.close()),
        ic.ICON_CLOSE_RADIAL:                   lambda: (ctx.close_animated(),self.viewport.controller.set_handles(['t'])),
    }

    def move_ctx():ctx.move(self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )
    config.callbackR = { ic.ICON_CLOSE_RADIAL: lambda: key_check_continuous(callback=move_ctx, key='r', interval=4) }




    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=mouse_pos,
        config=config
    )

def execute_plugin(window):
    obj_att_mng(window)