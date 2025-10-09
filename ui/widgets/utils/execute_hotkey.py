from PyQt6.QtCore import Qt, QPointF
import inspect

def hotkey_press(window, event):
    if event.key() == Qt.Key.Key_Escape:  window.close_menu()
    else:
        # Handle hotkey presses
        key = event.text().lower()
        for item in window.processed_items:
            hotkey = window.config.hotkey_items.get(item.symbol, "").lower()
            if hotkey and key == hotkey:
                if not item.editable:
                    break
                # Trigger ripple animation with epicenter on the right side
                item_rect = item.boundingRect()
                ripple_x = item_rect.right()
                ripple_y = item_rect.center().y()
                item.ripple_center = QPointF(ripple_x, ripple_y)
                item.itemColor = item.hover_color
                item._start_ripple()
                # Execute callback
                callback = window.config.callbackL.get(item.symbol)
                if callback:
                    if item.toggle_values:
                        item._toggle_state()
                        value = item._toggle_value
                        if len(inspect.signature(callback).parameters) > 0:
                            callback(value)
                        else:
                            callback()
                    elif item.slider_values:
                        value = item._slider_value
                        if len(inspect.signature(callback).parameters) > 0:
                            callback(value)
                        else:
                            callback()
                    else:
                        callback()
                    if window.config.auto_close:
                        window.close_animated()
                break