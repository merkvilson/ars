from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.key_check import key_check_continuous


from PyQt6.QtGui import QCursor
from PyQt6.QtCore import QPoint

def obj_primitive_ctx(self, position, callback):

    
    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return
    obj = selected[0]


    config = ContextMenuConfig()
    config.anchor = "+y"
    config.close_on_outside = False
    config.auto_close = False
    config.show_value = True


    options_list = [
        ic.ICON_AXIS_X,
        ic.ICON_AXIS_Y,
        ic.ICON_AXIS_Z,
        ic.ICON_RADIUS,
        ic.ICON_RADIUS_INNER,
        ic.ICON_LOD3,
        ic.ICON_ANGLE,
        ic.ICON_CLOSE_RADIAL,
    ]

    config.extra_distance = [0,(config.item_radius * 2) - 6 ]


    config.use_extended_shape_items = {ic.ICON_CLOSE_RADIAL: False,}


    config.additional_texts = {
        ic.ICON_AXIS_Y: "Size Y",
        ic.ICON_AXIS_X: "Size X",
        ic.ICON_AXIS_Z: "Size Z",
        ic.ICON_ANGLE: "Slice",
        ic.ICON_LOD3: "LOD",
        ic.ICON_RADIUS_INNER: "Inner Radius",
        ic.ICON_RADIUS: "Outer Radius",
    }

    config.slider_values = {
        ic.ICON_AXIS_X: (1,10,1),
        ic.ICON_AXIS_Y: (1,10,1),
        ic.ICON_AXIS_Z: (1,10,1),
        ic.ICON_RADIUS: (1,10,1),
        ic.ICON_RADIUS_INNER: (0,10,0),
        ic.ICON_LOD3: (1,50,30),
        ic.ICON_ANGLE: (0,360,360),
        }

    
    config.callbackL = {
        ic.ICON_AXIS_X: lambda val: obj.set_primitive_type(obj.primitive_type, width=val),
        ic.ICON_AXIS_Y: lambda val: obj.set_primitive_type(obj.primitive_type, height=val),
        ic.ICON_AXIS_Z: lambda val: obj.set_primitive_type(obj.primitive_type, depth=val),
        ic.ICON_LOD3: lambda val: obj.set_primitive_type(obj.primitive_type, lod=int(val)),
        ic.ICON_RADIUS: lambda val: obj.set_primitive_type(obj.primitive_type, radius=val),
        ic.ICON_ANGLE: lambda val: obj.set_primitive_type(obj.primitive_type, slice_start=val),
        ic.ICON_RADIUS_INNER: lambda val: obj.set_primitive_type(obj.primitive_type, radius_inner=val),

        ic.ICON_CLOSE_RADIAL: lambda: (ctx.close(), callback(self)),
    }

    def move_ctx():ctx.move(self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )
    config.callbackR = { ic.ICON_CLOSE_RADIAL: lambda: key_check_continuous(callback=move_ctx, key='r', interval=4) }


    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
