import math
from .b_button import BButton, BButtonConfig
from theme import StyleSheets
from theme.fonts.new_fonts import get_font
from theme.fonts.font_icons import *

from .utils.execute_hotkey import hotkey_press
from .utils import animated_effects  

from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QScrollArea,
    QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QStyle,
)
from PyQt6.QtGui import (
    QPainter, QColor,  QBrush, QCursor,
    QFont, QPainterPath, QRegion
)
from PyQt6.QtCore import (
    Qt, QPoint, QPointF, QRect, QRectF, QEvent, QTimer
)

from core.sound_manager import play_sound
from theme.fonts import font_icons as ic

class ContextMenuConfig:
    def __init__(self):
        self.menu_radius = 90
        self.item_radius = 22
        self.per_item_radius = {}
        self.extra_padding = 10
        self.extra_distance = [0, 0]
        self.start_angle = -math.pi / 2
        self.arc_span = 2 * math.pi
        self.hover_scale = 1.0
        self.distribution_mode = 'y'  # Options: "x", "y", "radial"
        self.anchor = "-y"  # Options: "-y", "+y", "-x", "+x"
        self.close_on_outside = True
        self.background_color = (255, 255, 255, 10)
        self.background_corner_radius = 22.0
        self.font = get_font(20)
        self.additional_font = QFont("Arial", 10)
        self.hotkey_text_color = QColor(255, 255, 255, 180) 
        self.callbackL = {}
        self.callbackR = {}
        self.callbackM = {}
        self.tooltips = {}
        self.symbol_colors = {}
        self.color = {}
        self.hover_color = {}
        self.additional_texts = {}
        self.hotkey_items = {}
        self.use_extended_shape = True
        self.use_extended_shape_items = {}
        self.auto_close = True
        self.slider_values = {}
        self.slider_color = {}
        self.toggle_values = {}
        self.toggle_color = {}
        self.toggle_hover_color = {}
        self.show_value = False
        self.show_value_items = {}
        self.show_symbol = True
        self.show_symbol_items = {}
        self.toggle_groups = []
        self.editable = True
        self.editable_items = {}
        self.progress_bar = False 
        self.progress_bar_items = {}
        self.image_items = {}
        self.clip_to_shape = True
        self.expand = None  # options: None, "x", "y", "xy"
        self.custom_widget_items = {}
        self.inner_widgets = {}
        self.incremental_values = {}

    def set_arc_range(self, start_degrees: float, end_degrees: float):
        self.start_angle = math.radians(start_degrees)
        self.arc_span = math.radians(end_degrees - start_degrees)


class ContextButtonWindow(QWidget):
    def __init__(self, parent, items, config, position):
        super().__init__(parent)

        self.config = config
        self.items = items

        # ---- Window flags / transparency ----
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        self._close_on_outside = getattr(config, "close_on_outside", False)
        if self._close_on_outside: QApplication.instance().installEventFilter(self)

        bg_color = getattr(config, "background_color", (255, 255, 255, 10))
        if isinstance(bg_color, QColor):
            bg_color = (bg_color.red(), bg_color.green(), bg_color.blue(), bg_color.alpha())
        self.bg_color = bg_color
        self.corner_radius = getattr(config, "background_corner_radius", 20)

        # Determine columns
        if items and isinstance(items[0], (list, tuple)):
            columns = items
        else:
            columns = [items]

        processed_columns = []
        toggle_groups = getattr(config, "toggle_groups", [])
        for col in columns:
            if isinstance(col, str) and col == "   ":
                processed_columns.append("h_spacer")
                continue
            processed_col = []
            for action in col:
                if isinstance(action, str):
                    if action == "   ":
                        processed_col.append("spacer")
                    else:
                        processed_col.append(action)
                elif isinstance(action, tuple):
                    sub_symbols = list(action)
                    processed_col.extend(sub_symbols)
                    if len(sub_symbols) == 1:
                        config.toggle_values[sub_symbols[0]] = (0, 1, 1)
                    else:
                        for idx, sub in enumerate(sub_symbols):
                            config.toggle_values[sub] = (0, 1, 1 if idx == 0 else 0)
                        toggle_groups.append(sub_symbols)
            processed_columns.append(processed_col)
        config.toggle_groups = toggle_groups

        self.processed_items = []
        for col in processed_columns:
            if isinstance(col, list):
                col_buttons = []
                for action in col:
                    if action == "spacer":
                        continue
                    if action in config.custom_widget_items:  # Added check
                        continue  # Skip creating BButton for custom widgets
                    button_config_kwargs = {
                        "symbol": action,
                        "radius": config.per_item_radius.get(action, config.item_radius),
                        "font": config.font,
                        "clip_to_shape": config.clip_to_shape,
                        "additional_font": config.additional_font,
                        "hover_scale": config.hover_scale,
                        "tooltip": config.tooltips.get(action, ""),
                        "callbackL": config.callbackL.get(action),
                        "callbackR": config.callbackR.get(action),
                        "callbackM": config.callbackM.get(action),
                        "use_extended_shape": config.use_extended_shape_items.get(action, config.use_extended_shape),
                        "auto_close": config.auto_close,
                        "slider_values": config.slider_values.get(action),
                        "show_value": config.show_value_items.get(action, config.show_value),
                        "show_symbol": config.show_symbol_items.get(action, config.show_symbol),
                        "editable": config.editable_items.get(action, config.editable),
                        "progress_bar": config.progress_bar_items.get(action, config.progress_bar),
                        "hotkey_text": config.hotkey_items.get(action),
                        "image_path": config.image_items.get(action),
                        "incremental_value": config.incremental_values.get(action),
                        "inner_widget": config.inner_widgets.get(action),
                    }
                    if action in config.additional_texts:
                        button_config_kwargs["additional_text"] = config.additional_texts[action]
                    if action in config.symbol_colors:
                        button_config_kwargs["symbol_color"] = config.symbol_colors[action]
                    if action in config.color:
                        button_config_kwargs["color"] = config.color[action]
                    if action in config.hover_color:
                        button_config_kwargs["hover_color"] = config.hover_color[action]
                    if action in config.additional_texts:
                        button_config_kwargs["additional_text_color"] = QColor(255, 255, 255, 180)
                    if action in config.hotkey_items:
                        button_config_kwargs["hotkey_text_color"] = config.hotkey_text_color
                    if action in config.slider_color:
                        button_config_kwargs["slider_color"] = config.slider_color[action]
                    toggle_val = config.toggle_values.get(action)
                    if toggle_val is not None:
                        if isinstance(toggle_val, bool):
                            button_config_kwargs["toggle_values"] = (0, 1, 1 if toggle_val else 0)
                        else:
                            button_config_kwargs["toggle_values"] = toggle_val
                    if action in config.toggle_color:
                        button_config_kwargs["toggle_color"] = config.toggle_color[action]
                    if action in config.toggle_hover_color:
                        button_config_kwargs["toggle_hover_color"] = config.toggle_hover_color[action]
                    button_config = BButtonConfig(**button_config_kwargs)
                    col_buttons.append(BButton(button_config))
                self.processed_items.extend(col_buttons)

        # ---- Handle toggle groups ----
        if getattr(config, "toggle_groups", None):
            for group_symbols in config.toggle_groups:
                group_buttons = [btn for btn in self.processed_items if btn.symbol in group_symbols]
                if group_buttons:
                    enabled_buttons = [btn for btn in group_buttons if btn._toggle_value > 0]
                    if len(enabled_buttons) > 1:
                        for btn in enabled_buttons[1:]:
                            btn._toggle_value = 0
                            btn._update_additional_text()
                            btn._update_colors()
                            btn._refresh_color()
                            btn.update()
                    for btn in group_buttons:
                        if btn.toggle_values is None:
                            btn.toggle_values = (0, 1, 0)
                            btn._toggle_value = 0
                        elif btn.toggle_values[1] != 1 or btn.toggle_values[0] != 0:
                            btn.toggle_values = (0, 1, 1 if btn._toggle_value > 0 else 0)
                            btn._toggle_value = btn.toggle_values[2]
                        btn.radio_group = group_buttons
                        btn._update_additional_text()
                        btn._update_colors()
                        btn._refresh_color()
                        btn.update()

        # ---- Window layout and sizing ----
        window_layout = QHBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(window_layout)


        if config.distribution_mode == 'radial':
            count = len(self.processed_items)
            center = QPointF(0, 0)

            center = QPointF(0, 0)
            if len(self.processed_items) > 0 and self.processed_items[0].symbol == ic.ICON_CLOSE_RADIAL:
                count_surround = len(self.processed_items) - 1
                positions = [center] + calc_positions(config, center, count_surround)
            else:
                positions = calc_positions(config, center, len(self.processed_items))
            #positions = calc_positions(config, center, count)
            bounding_rect = QRectF()
            for btn, pos in zip(self.processed_items, positions):
                full_rect = btn.boundingRect().united(btn.childrenBoundingRect())
                item_rect = full_rect.translated(pos.x() - full_rect.width() / 2, pos.y() - full_rect.height() / 2)
                bounding_rect = bounding_rect.united(item_rect)
            padding = config.extra_padding
            bounding_rect.adjust(-padding, -padding, padding, padding)
            width = bounding_rect.width()
            height = bounding_rect.height()
            if abs(config.arc_span - 2 * math.pi) < 1e-6:
                side = max(width, height)
                width = height = side
                self.corner_radius = side / 2
            shift = QPointF(-bounding_rect.left(), -bounding_rect.top())
            self.radial_center = shift
            scene = QGraphicsScene(0, 0, width, height)
            for btn, pos in zip(self.processed_items, positions):
                full_rect = btn.boundingRect().united(btn.childrenBoundingRect())
                btn_pos = pos + shift - QPointF(full_rect.width() / 2, full_rect.height() / 2)
                btn.setPos(btn_pos)
                scene.addItem(btn)
            view = QGraphicsView(scene)
            view.setFixedSize(int(width), int(height))
            view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            view.setFrameStyle(QFrame.Shape.NoFrame)
            view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            view.setBackgroundBrush(QBrush(Qt.BrushStyle.NoBrush))
            view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            view.setStyleSheet("background: transparent; border: none;")
            view.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            view.viewport().setStyleSheet("background: transparent;")
            window_layout.addWidget(view)
            self.setFixedSize(int(width), int(height))
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, width, height), self.corner_radius, self.corner_radius)
            region = QRegion(path.toFillPolygon().toPolygon())
            self.setMask(region)
        else:
            # ---- Content widget (must be transparent) ----
            content_widget = QWidget()
            content_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            content_widget.setStyleSheet("background: transparent;")
            main_layout = QHBoxLayout(content_widget) if config.distribution_mode == "y" else QVBoxLayout(content_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            expands = set(config.expand.lower()) if config.expand else set()
            has_h_spacer = any(isinstance(col, str) and col == "h_spacer" for col in processed_columns)
            if 'x' in expands and not has_h_spacer:
                main_layout.addStretch(1)
            for col in processed_columns:
                if isinstance(col, str) and col == "h_spacer":
                    main_layout.addStretch(1)
                    continue
                col_layout = QVBoxLayout() if config.distribution_mode == "y" else QHBoxLayout()
                col_layout.setContentsMargins(5, 5, 5, 5)
                has_spacer = "spacer" in col
                if 'y' in expands and not has_spacer:
                    col_layout.addStretch(1)
                for action in col:
                    if action == "spacer":
                        col_layout.addStretch(1)
                        continue
                    if action in config.custom_widget_items:  # Added check
                        custom_widget = config.custom_widget_items[action]
                        col_layout.addWidget(custom_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
                    else:
                        btn = next(btn for btn in self.processed_items if btn.symbol == action)
                        full_rect = btn.boundingRect().united(btn.childrenBoundingRect())
                        btn.setPos(-full_rect.left(), -full_rect.top())
                        scene = QGraphicsScene()
                        scene.addItem(btn)
                        scene.setSceneRect(0, 0, full_rect.width(), full_rect.height())
                        view = QGraphicsView(scene)
                        view.setFixedSize(int(full_rect.width()), int(full_rect.height()))
                        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                        view.setFrameStyle(QFrame.Shape.NoFrame)
                        view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
                        view.setBackgroundBrush(QBrush(Qt.BrushStyle.NoBrush))
                        view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                        view.setStyleSheet("background: transparent; border: none;")
                        view.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                        view.viewport().setStyleSheet("background: transparent;")
                        col_layout.addWidget(view, alignment=Qt.AlignmentFlag.AlignHCenter)
                if has_spacer:
                    pass
                elif 'y' in expands:
                    col_layout.addStretch(1)
                else:
                    col_layout.addStretch(1)
                main_layout.addLayout(col_layout)
            if 'x' in expands and not has_h_spacer:
                main_layout.addStretch(1)
            # ---- Scroll area (ensure transparency of viewport and contents) ----
            scroll_area = QScrollArea()
            scroll_area.setWidget(content_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            scroll_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            scroll_area.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            scroll_area.setStyleSheet(StyleSheets.CONTEXT_WINDOW_STYLE)
            scroll_area.viewport().setStyleSheet("background: transparent;")
            window_layout.addWidget(scroll_area)
            content_size = content_widget.sizeHint()
            base_x = content_size.width()
            max_height = content_size.height()
            height_unit = int(config.item_radius * 2.3)
            max_rows = max(len([a for a in col if a != "spacer"]) for col in processed_columns if isinstance(col, list)) if processed_columns else 0
            num_images = sum(1 for col in processed_columns if isinstance(col, list) for action in col if action != "spacer" and action in config.image_items)
            capped_items = min(max_rows + num_images * 2, 10)
            base_y = min(max_height, height_unit * capped_items)
            x = max(base_x, parent.width()) if 'x' in expands else base_x
            y = max(base_y, parent.height()) if 'y' in expands else base_y
            scroll_bar_width = QApplication.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
            if max_height > y:
                x += scroll_bar_width
            self.setFixedSize(x, y)
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width() + 2, self.height() + 2, self.corner_radius, self.corner_radius)
            region = QRegion(path.toFillPolygon().toPolygon())
            self.setMask(region)


    def get_value(self, item_symbol):
        for item in self.processed_items:
            if item.symbol == item_symbol:
                if hasattr(item, '_slider_value') and item._slider_value is not None:
                    return item._slider_value
                elif hasattr(item, '_toggle_value') and item._toggle_value is not None:
                    return item._toggle_value
                else:
                    return None
        return None

    def update_item(self, item_symbol, config_key, value):
        for item in self.processed_items:
            if item.symbol == item_symbol:
                item.set_updated_config(config_key, value)
                break

    def close_animated(self, duration: int = 250, end_radius: int = 50):
        play_sound("back")
        animated_effects.close_effect(self, duration, end_radius)

    def open_animated(self, duration: int = 200, start_radius: int = 50):
        if len(self.processed_items) < 20:
            animated_effects.open_effect(self, duration, start_radius)
        else:
            animated_effects.open_effect(self, 0, start_radius)

    def close_menu(self, time = 300):
        QTimer.singleShot(time, lambda: self.close_animated(150, 50))

    def keyPressEvent(self, event):
        hotkey_press(self, event)
        super().keyPressEvent(event)

    def paintEvent(self, event):
        # Paint only the rounded rectangle background
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        painter.setBrush(QColor(*self.bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)

    def mousePressEvent(self, event):
        if self.config.auto_close:
            self.close_animated()
        super().mousePressEvent(event)

    def eventFilter(self, watched, event):
        if self._close_on_outside and event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            pos = event.globalPosition().toPoint()
            local_pos = self.mapFromGlobal(pos)
            if not (self.rect().contains(local_pos) and self.mask().contains(local_pos)):
                self.close_animated()
                return False
        return super().eventFilter(watched, event)

    def closeEvent(self, event):
        if self._close_on_outside:
            QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)


def calc_positions(config, center_pos, count):
    if count == 0: return []
    
    def radial():
        radius = config.menu_radius
        if count == 1:
            angle = config.start_angle
            x = center_pos.x() + radius * math.cos(angle)
            y = center_pos.y() + radius * math.sin(angle)
            return [QPointF(x, y)]
        else:
            if abs(config.arc_span - 2 * math.pi) < 1e-6:
                angle_step = config.arc_span / count
            else:
                angle_step = config.arc_span / (count - 1)
            return [QPointF(center_pos.x() + radius * math.cos(config.start_angle + i * angle_step),
                            center_pos.y() + radius * math.sin(config.start_angle + i * angle_step))
                    for i in range(count)]
    
    modes = {'radial': lambda: radial(),}
    
    return modes.get(config.distribution_mode, lambda: [])()


def open_context(parent, items, position=None, config=None):
    play_sound("hover2")

    if config is None: config = ContextMenuConfig()

    # Now create the grid window with processed BButton instances
    global ctx_window
    ctx_window = ContextButtonWindow(parent, items, config, position)
    if position is None:
        position = QCursor.pos()

    if config.distribution_mode == 'radial':
        radial_center = ctx_window.radial_center
        menu_x = position.x() - int(radial_center.x()) + config.item_radius
        menu_y = position.y() - int(radial_center.y()) + config.item_radius
    else:
        # Handle different anchor positions
        if config.anchor == "-y":  # Open below cursor
            menu_x = position.x() - ctx_window.width() // 2
            menu_y = position.y() + 40
        elif config.anchor == "+y":  # Open above cursor
            menu_x = position.x() - ctx_window.width() // 2
            menu_y = position.y() - ctx_window.height() - 10
        elif config.anchor == "-x":  # Open to the right of cursor
            menu_x = position.x() + 10
            menu_y = position.y() - ctx_window.height() // 2
        elif config.anchor == "+x":  # Open to the left of cursor
            menu_x = position.x() - ctx_window.width() - 10
            menu_y = position.y() - ctx_window.height() // 2

    parent_rect = parent.geometry()
    menu_pos = QPoint(menu_x+config.extra_distance[0], menu_y+config.extra_distance[1])
    menu_rect = QRect(menu_pos, ctx_window.size())
    if menu_rect.right() > parent_rect.right():
        menu_pos.setX(parent_rect.right() - menu_rect.width())
    if menu_rect.left() < parent_rect.left():
        menu_pos.setX(parent_rect.left())
    if menu_rect.bottom() > parent_rect.bottom():
        menu_pos.setY(parent_rect.bottom() - menu_rect.height())
    if menu_rect.top() < parent_rect.top():
        menu_pos.setY(parent_rect.top())
    ctx_window.move(menu_pos.x(), menu_pos.y())

    ctx_window.open_animated()
    ctx_window.raise_()
    ctx_window.activateWindow()
    return ctx_window