from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic


from PyQt6.QtGui import QCursor, QColor
from PyQt6.QtCore import QPoint

def obj_scale(self, position, callback):

    
    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return
    obj = selected[0]


    config = ContextMenuConfig()
    config.anchor = "+y"
    config.close_on_outside = False
    config.auto_close = True
    config.show_value = True


    options_list = [
        ic.ICON_AXIS_X,
        ic.ICON_AXIS_Y,
        ic.ICON_AXIS_Z,
        ic.ICON_CLOSE_RADIAL,
    ]

    config.extra_distance = [0,(config.item_radius * 2) - 6 ]


    config.use_extended_shape_items = {ic.ICON_CLOSE_RADIAL: False,}


    config.additional_texts = {
        ic.ICON_AXIS_Y: "Size Y",
        ic.ICON_AXIS_X: "Size X",
        ic.ICON_AXIS_Z: "Size Z",
    }

    config.slider_values = {
        ic.ICON_AXIS_X: (1,10000,obj.get_scale()[0]*100),
        ic.ICON_AXIS_Y: (1,10000,obj.get_scale()[1]*100),
        ic.ICON_AXIS_Z: (1,10000,obj.get_scale()[2]*100),
        ic.ICON_CLOSE_RADIAL: (0,1,0),
        }

    config.incremental_values = {ic.ICON_AXIS_X: 100, ic.ICON_AXIS_Y: 100, ic.ICON_AXIS_Z: 100,}
    
    config.callbackL = {
        ic.ICON_AXIS_X:       lambda value: obj.set_scale((value/100, obj.get_scale()[1], obj.get_scale()[2])),
        ic.ICON_AXIS_Y:       lambda value: obj.set_scale((obj.get_scale()[0], value/100, obj.get_scale()[2])),
        ic.ICON_AXIS_Z:       lambda value: obj.set_scale((obj.get_scale()[0], obj.get_scale()[1], value/100)),
        ic.ICON_CLOSE_RADIAL: lambda: (ctx.close(), callback(self)),
    }

    config.callbackR = { ic.ICON_CLOSE_RADIAL: lambda value: ctx.move(  self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )
    }

    config.slider_color = {ic.ICON_CLOSE_RADIAL: QColor(150, 150, 150, 0)}



    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
