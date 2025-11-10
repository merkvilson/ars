from PyQt6.QtGui import QColor, QBrush, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF



def set_updated_config(widget, key: str, value):
    # Import widget classes inside the function to avoid circular imports
    from .b_button import BButton

    # Common color conversion for keys ending with '_color'
    if key.endswith("_color") and isinstance(value, str):
        value = QColor(value)

    # Update the config attribute if it exists
    if hasattr(widget.config, key):
        setattr(widget.config, key, value)

    # Widget-specific updates
    if isinstance(widget, BButton):
        # Handle BButton specific keys
        if key == "symbol":
            widget.symbol = value
            symbol_item = widget.childItems()[0] if widget.childItems() else None
            if symbol_item:
                symbol_item.setPlainText(value)
                bounding = symbol_item.boundingRect()
                symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)
                widget.update()
        

        elif key == "additional_text":
            widget.additional_text = value
            if widget.additional_text_item:
                widget.additional_text_item.setPlainText(value)
                add_bounding = widget.additional_text_item.boundingRect()
                main_text_item = widget.childItems()[0] if widget.childItems() else None
                if main_text_item:
                    main_bounding = main_text_item.boundingRect()
                    main_right = main_bounding.width() / 2
                    padding = 10
                    add_left = main_right + padding
                    widget.additional_text_item.setPos(add_left, -add_bounding.height() / 2)
                widget.update()
            elif value:
                widget.additional_text_item = QGraphicsTextItem(value, widget)
                widget.additional_text_item.setFont(widget._additional_font)
                widget.additional_text_item.setDefaultTextColor(widget._additional_text_color)
                add_bounding = widget.additional_text_item.boundingRect()
                main_text_item = widget.childItems()[0] if widget.childItems() else None
                if main_text_item:
                    main_bounding = main_text_item.boundingRect()
                    main_right = main_bounding.width() / 2
                    padding = 10
                    add_left = main_right + padding
                    widget.additional_text_item.setPos(add_left, -add_bounding.height() / 2)
                widget.update()
        

        elif key == "color":
            widget.normal_color = value
            if not widget.isUnderMouse():
                widget._item_color = value
                widget.current_brush = QBrush(value)
                widget.pen = QPen(value.darker(), 0)
                widget.update()
        

        elif key == "hover_color":
            widget.hover_color = value
            if widget.isUnderMouse():
                widget._item_color = value
                widget.current_brush = QBrush(value)
                widget.pen = QPen(value.darker(), 0)
                widget.update()
        

        elif key == "symbol_color":
            widget._symbol_color = value
            symbol_item = widget.childItems()[0] if widget.childItems() else None
            if symbol_item:
                symbol_item.setDefaultTextColor(value)
                widget.update()
        

        elif key == "additional_text_color":
            widget._additional_text_color = value
            if widget.additional_text_item:
                widget.additional_text_item.setDefaultTextColor(value)
                widget.update()
        

        elif key == "font":
            widget._font = value
            symbol_item = widget.childItems()[0] if widget.childItems() else None
            if symbol_item:
                symbol_item.setFont(value)
                bounding = symbol_item.boundingRect()
                symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)
                widget.update()
        

        elif key == "additional_font":
            widget._additional_font = value
            if widget.additional_text_item:
                widget.additional_text_item.setFont(value)
                add_bounding = widget.additional_text_item.boundingRect()
                widget.additional_text_item.setPos(widget.additional_text_item.pos().x(), -add_bounding.height() / 2)
                widget.update()
        

        elif key == "hover_scale":
            widget.hover_scale = float(value)
            if widget.isUnderMouse():
                widget.setScale(widget.hover_scale)
                widget.update()
        

        elif key == "tooltip":
            widget.setToolTip(value)
        

        elif key == "callbackL":
            widget.callbackL = value
        

        elif key == "callbackR":
            widget.callbackR = value
        

        elif key == "callbackM":
            widget.callbackM = value
        

        elif key == "use_extended_shape":
            widget.use_extended_shape = value
            normal_width = 2 * widget.radius
            if value:
                new_width = 4 * normal_width
                left = -widget.radius
                widget._bounding = QRectF(left, -widget.radius, new_width, 2 * widget.radius)
            else:
                widget._bounding = QRectF(-widget.radius, -widget.radius, 2 * widget.radius, 2 * widget.radius)
            widget.ripple_end_radius = max(widget._bounding.width(), widget._bounding.height()) / 2 * 1.5
            widget.update()
        

        elif key == "auto_close":
            widget.auto_close = value
        

        elif key == "radius":
            widget.radius = value
            normal_width = 2 * widget.radius
            if widget.use_extended_shape:
                new_width = 4 * normal_width
                left = -widget.radius
                widget._bounding = QRectF(left, -widget.radius, new_width, 2 * widget.radius)
            else:
                widget._bounding = QRectF(-widget.radius, -widget.radius, 2 * widget.radius, 2 * widget.radius)
            widget.ripple_end_radius = max(widget._bounding.width(), widget._bounding.height()) / 2 * 1.5
            widget.update()
        

        elif key == "show_value":
            widget.show_value = value
            widget._update_additional_text()
            widget.update()


        elif key == "show_symbol":
            widget.show_symbol = value
            widget._symbol_color = QColor(widget.config.symbol_color.red(), widget.config.symbol_color.green(), widget.config.symbol_color.blue(), 255 if value else 0)
            widget.main_symbol_item.setDefaultTextColor(widget._symbol_color)
            widget.update()
        

        elif key == "editable":
            widget.editable = value
            widget.setAcceptHoverEvents(widget.editable)
            widget.setAcceptedMouseButtons(Qt.MouseButton.AllButtons if widget.editable else Qt.MouseButton.NoButton)
            if not value:
                widget.normal_color = widget.config.color.darker(150)
                widget.hover_color = widget.normal_color
                widget._symbol_color = widget.config.symbol_color.darker(150)
                widget._additional_text_color = widget.config.additional_text_color.darker(150)
                widget.slider_color = widget.config.slider_color.darker(150)
                widget.toggle_color = widget.config.toggle_color.darker(150)
                widget.toggle_hover_color = widget.toggle_color
            elif value:
                widget.normal_color = widget.config.color
                widget.hover_color = widget.config.hover_color
                widget._symbol_color = widget.config.symbol_color
                widget._additional_text_color = widget.config.additional_text_color
                widget.slider_color = widget.config.slider_color
                widget.toggle_color = widget.config.toggle_color
                widget.toggle_hover_color = widget.config.toggle_hover_color
            if widget.slider_values:
                normal_alpha = int(widget.normal_color.alpha() * 0.7)
                hover_alpha = int(widget.hover_color.alpha() * 0.7)
                widget.normal_color.setAlpha(normal_alpha)
                widget.hover_color.setAlpha(hover_alpha)
            if not widget.show_symbol:
                widget._symbol_color.setAlpha(0)
            widget.main_symbol_item.setDefaultTextColor(widget._symbol_color)
            if widget.additional_text_item:
                widget.additional_text_item.setDefaultTextColor(widget._additional_text_color)
            widget._update_colors()
            widget._refresh_color()
            widget.update()
        

        elif key == "progress_bar":
            widget.config.progress_bar = value
            widget.progress_bar = value
            if value:
                widget.slider_values = (0, 100, 0)
                widget._slider_value = 0
                widget.slider_color = QColor(120, 150, 255, 230)
                widget.editable = False
                widget._update_colors()
                widget._refresh_color()
                widget._update_additional_text()
                    
                widget.setAcceptHoverEvents(widget.editable)
                widget.setAcceptedMouseButtons(Qt.MouseButton.AllButtons if widget.editable else Qt.MouseButton.NoButton)
            else:
                widget.slider_values = None
                widget._slider_value = None
                widget.slider_color = widget.config.slider_color
                widget.editable = True
                if hasattr(widget, 'slider_handle') and widget.slider_handle:
                    widget.slider_handle.setParentItem(None)
                    widget.slider_handle = None
                widget.normal_color = widget.config.color
                widget.hover_color = widget.config.hover_color
                widget._update_additional_text()
                widget._update_colors()
                widget._refresh_color()
                widget.setAcceptHoverEvents(widget.editable)
                widget.setAcceptedMouseButtons(Qt.MouseButton.AllButtons if widget.editable else Qt.MouseButton.NoButton)
            widget.update()
        

        elif key == "slider_values":  # New handling for slider_values
            if isinstance(value, tuple) and len(value) == 3:
                widget.slider_values = value
                widget._slider_value = value[2]
                if widget.slider_values:
                    normal_alpha = int(widget.normal_color.alpha() * 0.7)
                    hover_alpha = int(widget.hover_color.alpha() * 0.7)
                    widget.normal_color = QColor(widget.normal_color.red(), widget.normal_color.green(), widget.normal_color.blue(), normal_alpha)
                    widget.hover_color = QColor(widget.hover_color.red(), widget.hover_color.green(), widget.hover_color.blue(), hover_alpha)
                if not hasattr(widget, 'slider_handle') or not widget.slider_handle:
                    widget._create_slider_handle()
                widget._update_additional_text()
                    
                widget._update_colors()
                widget._refresh_color()
                widget.update()
            else:
                widget.slider_values = None
                widget._slider_value = None
                widget.normal_color = widget.config.color
                widget.hover_color = widget.config.hover_color
                widget._update_additional_text()
                if hasattr(widget, 'slider_handle') and widget.slider_handle:
                    widget.slider_handle.setParentItem(None)
                    widget.slider_handle = None
                widget._update_colors()
                widget._refresh_color()
                widget.update()

        

        elif key == "progress":
            if widget.slider_values:
                min_val, max_val, _ = widget.slider_values
                new_value = max(min_val, min(max_val, value))  # Clamp to min/max
                widget._slider_value = new_value
                widget.slider_values = (min_val, max_val, new_value)
                widget._update_additional_text()
                    
                #widget._update_colors()
                #widget._refresh_color()
                widget.update()


        elif key == "image_path":
            widget.image_path = value
            widget.pixmap = None
            if value:
                widget.pixmap = QPixmap(value)
                if widget.pixmap.isNull():
                    widget.pixmap = None
                    print(f"Warning: Failed to load image from {value}")
            widget.update()


        elif key == "toggle_values":
            if value is True:
                widget.toggle_values = (0, 1, 1)
                widget._toggle_value = 1
            elif value is False:
                widget.toggle_values = (0, 1, 0)
                widget._toggle_value = 0
            elif isinstance(value, tuple) and len(value) >= 3:
                widget.toggle_values = value[:3]
                widget._toggle_value = value[2]
            else:
                widget.toggle_values = None
                widget._toggle_value = None
            widget._update_additional_text()
            widget._update_colors()
            widget._refresh_color()
            widget.update()

        elif key == "hotkey_text":
            widget.hotkey_text = value
            if value:
                widget._create_hotkey_items()
                for item in widget.hotkey_text_items + widget.hotkey_outline_items:
                    item.setVisible(widget.show_hotkey)
            else:
                for item in widget.hotkey_text_items + widget.hotkey_outline_items:
                    item.setParentItem(None)
                widget.hotkey_text_items = []
                widget.hotkey_outline_items = []
            widget.update()

        elif key == "show_hotkey":
            widget.show_hotkey = value
            for item in widget.hotkey_text_items + widget.hotkey_outline_items:
                item.setVisible(value)
            widget.update()

        elif key == "clip_to_shape":

            widget.config.clip_to_shape = bool(value)
            widget.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
                widget.config.clip_to_shape
            )
            widget.update()

    else:
        print(f"Unsupported widget type: {type(widget)}")