from PyQt6.QtWidgets import (
    QGraphicsTextItem,
    QGraphicsObject,
    QGraphicsRectItem,QGraphicsItem)

from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QPainterPath,
    QPixmap,)

from PyQt6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    pyqtProperty,
    QRectF,
    QPointF,
    QTimer,)


from dataclasses import dataclass, field
from typing import Optional, Callable, Tuple, Any


import math
import inspect
from theme.fonts.new_fonts import get_font
from .widget_control import set_updated_config
from core.cursor_modifier import CursorModifier

import os
from core.sound_manager import play_sound

class SliderHandle(QGraphicsRectItem):
    """Custom handle for the slider, handling drag events."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_button = parent
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)
        self._is_dragging = False
        self._drag_button = None
        self.is_incremental = parent.incremental_value
        self.drag_offset = 0.0

    def mousePressEvent(self, event):
        if self.parent_button.slider_values and self.parent_button.editable:
            self._is_dragging = True
            self._drag_button = event.button()
            self.parent_button._is_dragging = True
            self.parent_button._drag_button = self._drag_button
            self.drag_offset = event.pos().x()
            self.grabMouse()
            if self.is_incremental:
                self.parent_button.update_timer.start()
            self.parent_button._update_slider_value(self.mapToParent(event.pos()))
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.parent_button.slider_values and self.parent_button.editable:
            self.parent_button.ripple_center = self.mapToParent(event.pos())
            self.parent_button._start_ripple()
            self.ungrabMouse()

            self._is_dragging = False
            self._drag_button = None
            self.parent_button._is_dragging = False
            self.parent_button._drag_button = None

            if self.is_incremental:
                self.parent_button.update_timer.stop()
                self.parent_button._snap_handle_to_center()
            event.accept()


    def mouseMoveEvent(self, event):
        if self._is_dragging and self.parent_button.slider_values and self.parent_button.editable:
            parent_pos = self.mapToParent(event.pos())
            self.parent_button._update_slider_value(parent_pos)
            event.accept()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = self.parent_button.shape()
        painter.setClipPath(path)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRect(self.rect())

class RoundedRectOutline(QGraphicsRectItem):
    """Custom QGraphicsRectItem with rounded corners for the hotkey text outline."""
    def __init__(self, corner_radius=6, parent=None):
        super().__init__(parent)
        self.corner_radius = corner_radius
        self.parent_button = parent
        # Initialize brush to match parent button's current brush
        if parent:
            self.setBrush(parent.current_brush)
        else:
            self.setBrush(QBrush(QColor(0, 0, 0, 0)))

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.corner_radius, self.corner_radius)
        painter.setClipPath(path)
        # Use the parent button's current brush for background
        if self.parent_button:
            painter.setBrush(self.parent_button.current_brush)
        else:
            painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawPath(path)


@dataclass
class BButtonConfig:
    symbol: str = ""
    radius: int = 20
    color: QColor = field(default_factory=lambda: QColor(70, 70, 70, 200))
    hover_color: QColor = field(default_factory=lambda: QColor(150, 150, 150, 200))
    symbol_color: QColor = field(default_factory=lambda: QColor(255, 255, 255, 180))
    additional_text_color: QColor = field(default_factory=lambda: QColor(255, 255, 255, 180))
    hotkey_text_color: QColor = field(default_factory=lambda: QColor(255, 255, 255, 180))
    font: QFont = field(default_factory=lambda: get_font(16))
    additional_font: QFont = field(default_factory=lambda: QFont("Arial", 10))
    hover_scale: float = 1.1
    tooltip: str = ""
    callbackL: Optional[Callable] = None
    callbackR: Optional[Callable] = None
    callbackM: Optional[Callable] = None
    additional_text: Optional[str] = None
    hotkey_text: Optional[str] = None
    use_extended_shape: bool = False
    auto_close: bool = False
    slider_values: Optional[Tuple[int, int, int]] = None
    slider_color: QColor = field(default_factory=lambda: QColor(150, 150, 150, 150))
    toggle_values: Optional[Any] = None
    toggle_color: QColor = field(default_factory=lambda: QColor(100, 120, 170, 200))
    toggle_hover_color: QColor = field(default_factory=lambda: QColor(120, 150, 255, 230))
    show_value: bool = False
    show_symbol: bool = True
    editable: bool = True
    progress_bar: bool = False
    image_path: Optional[str] = None
    clip_to_shape: bool = True
    incremental_value: bool = False


class BButton(QGraphicsObject):
    """Bubble button with configurable properties, animation support, and slider/toggle functionality."""
    def __init__(self, config: BButtonConfig):
        super().__init__()
        self.config = config
        self.symbol = config.symbol
        self.additional_text = config.additional_text
        self.hotkey_text = config.hotkey_text
        self.hotkey_text_items = []
        self.hotkey_outline_items = []
        self.use_extended_shape = config.use_extended_shape
        self.auto_close = config.auto_close
        self.radius = config.radius
        self.additional_text_item = None
        self.slider_color = config.slider_color
        self.toggle_color = config.toggle_color
        self.toggle_hover_color = config.toggle_hover_color
        self.show_value = config.show_value
        self.show_symbol = config.show_symbol
        self.editable = config.editable
        self.progress_bar = config.progress_bar
        self.incremental_value = config.incremental_value


        self.image_path = config.image_path  
        self.pixmap = None 
        if self.image_path:
            self.pixmap = QPixmap(self.image_path) 
            if self.pixmap.isNull():
                self.pixmap = None
                print(f"Warning: Failed to load image from {self.image_path}") 


        if self.progress_bar:
            self.slider_values = (0, 100, 0)
            self._slider_value = 0
            self.slider_color = QColor(120, 150, 255, 230)
            self.editable = False
        self._is_dragging = False
        self._drag_button = None
        self.slider_handle = None
        self.radio_group = None
        
        # Handle slider_values with safety check
        if isinstance(config.slider_values, tuple) and len(config.slider_values) >= 3:
            self.slider_values = config.slider_values[:3]
            self._slider_value = config.slider_values[2]
        else:
            self.slider_values = None
            self._slider_value = None
        
        # Handle toggle_values, including boolean interpretation
        if config.toggle_values is True:
            self.toggle_values = (0, 1, 1)
            self._toggle_value = 1
        elif config.toggle_values is False:
            self.toggle_values = (0, 1, 0)
            self._toggle_value = 0
        elif isinstance(config.toggle_values, tuple) and len(config.toggle_values) >= 3:
            self.toggle_values = config.toggle_values[:3]
            self._toggle_value = config.toggle_values[2]
        else:
            self.toggle_values = None
            self._toggle_value = None
        

        if self.use_extended_shape:
            height = (6 * self.radius) if self.image_path else (2 * self.radius)
            self._bounding = QRectF( -self.radius,  -self.radius, 8 * self.radius, height)
        else:
            self._bounding = QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)


        self.normal_color = config.color
        self.hover_color = config.hover_color
        if self.slider_values:
            normal_alpha = int(self.normal_color.alpha() * 0.7)
            hover_alpha = int(self.hover_color.alpha() * 0.7)
            self.normal_color = QColor(self.normal_color.red(), self.normal_color.green(), self.normal_color.blue(), normal_alpha)
            self.hover_color = QColor(self.hover_color.red(), self.hover_color.green(), self.hover_color.blue(), hover_alpha)
        
        self._update_colors()
        self._item_color = self.normal_color
        self.current_brush = QBrush(self._item_color)
        self.pen = QPen(self._item_color.darker(), 0)
        
        interact = self.editable
        if interact:
            self.setAcceptHoverEvents(True)
            self.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)
        if config.clip_to_shape:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)


        self.original_scale = 1.0
        self.hover_scale = float(config.hover_scale) if not self.use_extended_shape else 1.01
        self.setScale(self.original_scale)
        self.setOpacity(1.0)
        self.setToolTip(config.tooltip if not self.additional_text and not self.hotkey_text else "")

        # Main Symbol
        self.main_symbol_item = QGraphicsTextItem(self.symbol, self)
        self._symbol_color = config.symbol_color
        if not self.show_symbol:
            self._symbol_color = QColor(self._symbol_color.red(), self._symbol_color.green(), self._symbol_color.blue(), 0)
        self.main_symbol_item.setDefaultTextColor(self._symbol_color)
        self._font = config.font
        self.main_symbol_item.setFont(self._font)
        bounding = self.main_symbol_item.boundingRect()
        self.main_symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)

        # Additional Text (including slider/toggle value if applicable)
        initial_base = self.additional_text if self.additional_text else ""
        if self.show_value:
            if self.slider_values:
                initial_value = f" {int(round(self._slider_value))}{"%" if self.progress_bar else ""}"
            elif self.toggle_values:
                min_val, max_val, _ = self.toggle_values
                if min_val == 0 and max_val == 1:
                    initial_value = f"   {'On' if self._toggle_value else 'Off'}"
                else:
                    initial_value = f" {self._toggle_value}"
            else:
                initial_value = ""
        else:
            initial_value = ""
        initial_text = initial_base + initial_value
        if initial_text:
            self.additional_text_item = QGraphicsTextItem(self)
            self._additional_font = config.additional_font
            self.additional_text_item.setFont(self._additional_font)
            self._additional_text_color = config.additional_text_color
            self.additional_text_item.setDefaultTextColor(self._additional_text_color)
            self.additional_text_item.setHtml(initial_text)
            add_bounding = self.additional_text_item.boundingRect()
            main_right = bounding.width() / 2
            padding = 3
            add_left = main_right + padding
            self.additional_text_item.setPos(add_left, -add_bounding.height() / 2)

        # Hotkey Text setup
        self._hotkey_text_color = config.hotkey_text_color
        if self.hotkey_text:
            self._create_hotkey_items()

        # Slider Handle
        if self.slider_values and interact:
            self.slider_handle = SliderHandle(self)
            self.center_x = self._bounding.center().x()
            self.current_offset = 0.0
            cy = self._bounding.center().y()
            h = self._bounding.height()

            handle_size = 300
            self.handle_r = handle_size / 2
            self.slider_handle.setRect(QRectF(-self.handle_r, self._bounding.top() - cy, handle_size, h))
            self.slider_handle.setBrush(QBrush(QColor(255, 255, 255, 0)))
            self.slider_handle.setPen(QPen(Qt.PenStyle.NoPen))

            if self.incremental_value:
                self.update_timer = QTimer(self)
                self.update_timer.setInterval(50)
                self.update_timer.timeout.connect(self._increment_value)

            self._update_handle_position()
            self.slider_handle.setZValue(1.0)

            if self.incremental_value: cursor_type = ("arrow-bar-both","arrow-bar-left","arrow-bar-right") 
            else: cursor_type = ("caret-left-right","caret-left","caret-right") 

            self._cursor_modifier = CursorModifier(
                trigger_widget=self.slider_handle,
                axis="x",
                bg_color=QColor(70, 70, 70, 200) if self.incremental_value else None,
                #target=self.slider_handle.scenePos().toPoint(),
                target = None,
                cursor_type=cursor_type,
                anchor="center",
                teleport_back=self.incremental_value)


        # Ripple effect
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self.ripple_center = self.boundingRect().center()
        self.ripple_end_radius = max(self._bounding.width(), self._bounding.height()) / 2 * 1.5
        self.ripple_anim_group = None

        # Default callbacks
        def default_callback(value=None):
            action = "clicked" if value is None else f"set to {value}"
            print(f"{self.symbol} {action}")

        self.callbackL = config.callbackL if config.callbackL else default_callback
        self.callbackR = config.callbackR if config.callbackR else default_callback
        self.callbackM = config.callbackM if config.callbackM else default_callback

    def _create_hotkey_items(self):
        # Clear old hotkey items
        for item in self.hotkey_text_items:
            item.setParentItem(None)
        self.hotkey_text_items = []
        for item in self.hotkey_outline_items:
            item.setParentItem(None)
        self.hotkey_outline_items = []

        words = self.hotkey_text.split()
        if not words:
            return

        space_between = 4  # Pixels between words
        right_edge = self._bounding.right()
      
        outside_offset = - 30
        current_left = right_edge + outside_offset

        for word in words:
            text_item = QGraphicsTextItem(self)
            text_item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            text_item.setDefaultTextColor(self._hotkey_text_color)
            text_item.setPlainText(word)
            bounding = text_item.boundingRect()
            text_item.setPos(current_left, -bounding.height() / 2)
            self.hotkey_text_items.append(text_item)

            outline_item = RoundedRectOutline(corner_radius=6, parent=self)
            outline_padding = 1
            outline_rect = QRectF(
                current_left - outline_padding,
                -bounding.height() / 2 - outline_padding,
                bounding.width() + 2 * outline_padding,
                bounding.height() + 2 * outline_padding
            )
            outline_item.setRect(outline_rect)
            outline_item.setPen(QPen(self._hotkey_text_color, 1))
            # Set background to match the button's current brush
            outline_item.setBrush(self.current_brush)
            outline_item.setZValue(-1)
            self.hotkey_outline_items.append(outline_item)

            current_left += bounding.width() + space_between

    def _update_colors(self):
        if self.toggle_values and self._toggle_value > 0:
            self.normal_color = self.toggle_color
            self.hover_color = self.toggle_hover_color
        else:
            self.normal_color = self.config.color
            self.hover_color = self.config.hover_color
        if self.slider_values:
            normal_alpha = int(self.normal_color.alpha() * 0.7)
            hover_alpha = int(self.hover_color.alpha() * 0.7)
            self.normal_color = QColor(self.normal_color.red(), self.normal_color.green(), self.normal_color.blue(), normal_alpha)
            self.hover_color = QColor(self.hover_color.red(), self.hover_color.green(), self.hover_color.blue(), hover_alpha)

    def _refresh_color(self):
        if hasattr(self, 'color_anim') and self.color_anim and self.color_anim.state() == QPropertyAnimation.State.Running:
            self.color_anim.stop()
        if not self.editable:
            self.itemColor = self.normal_color
        elif self.scale() == self.hover_scale:
            self.itemColor = self.hover_color
        else:
            self.itemColor = self.normal_color

    def _toggle_state(self):
        if not self.editable or not self.toggle_values:
            return
        if self.radio_group:
            if self._toggle_value == 0:
                self._toggle_value = 1
                for other in self.radio_group:
                    if other != self and other._toggle_value != 0:
                        other._toggle_value = 0
                        other._update_additional_text()
                        other._update_colors()
                        other._refresh_color()
                        other.update()
        else:
            min_val, max_val, _ = self.toggle_values
            self._toggle_value += 1
            if self._toggle_value > max_val:
                self._toggle_value = min_val
        self._update_additional_text()
        self._update_colors()
        self._refresh_color()
        self.update()


    def set_updated_config(self, key: str, value):
        """Update a specific configuration property in real-time."""
        set_updated_config(self, key, value)



    @pyqtProperty(QColor)
    def itemColor(self):
        return self._item_color

    @itemColor.setter
    def itemColor(self, color):
        self._item_color = color
        self.current_brush = QBrush(color)
        self.pen = QPen(color.darker(), 0)
        # Update hotkey outline items' background to match
        for outline_item in self.hotkey_outline_items:
            outline_item.setBrush(self.current_brush)
        self.update()

    @pyqtProperty(float)
    def ripple_radius(self):
        return self._ripple_radius

    @ripple_radius.setter
    def ripple_radius(self, value):
        self._ripple_radius = value
        self.update()

    @pyqtProperty(float)
    def ripple_opacity(self):
        return self._ripple_opacity

    @ripple_opacity.setter
    def ripple_opacity(self, value):
        self._ripple_opacity = value
        self.update()

    def boundingRect(self):
        return self._bounding

    def shape(self):
        path = QPainterPath()
        if self.use_extended_shape:
            path.addRoundedRect(self._bounding, self.radius, self.radius)
        else:
            path.addEllipse(self._bounding)
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self.pen)
        painter.setBrush(self.current_brush)
        if self.use_extended_shape:
            painter.drawRoundedRect(self._bounding, self.radius, self.radius)
        else:
            painter.drawEllipse(self._bounding)

        if self.pixmap: 
            painter.save()
            path = self.shape()
            painter.setClipPath(path)
            scaled_pixmap = self.pixmap.scaled(
                self._bounding.size().toSize(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            draw_pos = self._bounding.center() - QPointF(
                scaled_pixmap.width() / 2,
                scaled_pixmap.height() / 2
            )
            painter.drawPixmap(int(draw_pos.x()), int(draw_pos.y()), scaled_pixmap)
            painter.restore()


        if self.slider_values:
            min_val, max_val, _ = self.slider_values
            painter.save()
            path = self.shape()
            painter.setClipPath(path)
            slider_brush = QBrush(self.slider_color)
            painter.setBrush(slider_brush)
            painter.setPen(Qt.PenStyle.NoPen)
            progress_ratio = (self._slider_value - min_val) / (max_val - min_val)
            progress_width = self._bounding.width() * progress_ratio
            slider_rect = QRectF(self._bounding.left(), self._bounding.top(), progress_width, self._bounding.height())
            if self.use_extended_shape:
                painter.drawRoundedRect(slider_rect, self.radius, self.radius)
            else:
                painter.drawEllipse(slider_rect)
            painter.restore()



        if self._ripple_opacity > 0:
            painter.save()
            path = self.shape()
            painter.setClipPath(path)
            ripple_color = QColor(255, 255, 255, int(255 * self._ripple_opacity * 0.8))
            painter.setBrush(QBrush(ripple_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(self.ripple_center, self._ripple_radius, self._ripple_radius)
            painter.restore()

    def hoverEnterEvent(self, event):
        play_sound("hover")
        if not self.editable:
            return
        self.itemColor = self.hover_color
        self.setScale(self.hover_scale)
        if self.additional_text_item:
            bold_font = QFont(self._additional_font)
            bold_font.setWeight(QFont.Weight.Bold)
            self.additional_text_item.setFont(bold_font)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.editable:
            return
        was_ripple_active = False
        if self.ripple_anim_group:
            self.ripple_anim_group.stop()
            self._reset_ripple()
            was_ripple_active = True
        if not was_ripple_active:
            self.itemColor = self.normal_color
        self.setScale(self.original_scale)
        if self.additional_text_item:
            self.additional_text_item.setFont(self._additional_font)
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if not self.editable:
            return
        if self.ripple_anim_group:
            self.ripple_anim_group.stop()
            self._reset_ripple()
        self.itemColor = self.hover_color
        self.ripple_center = event.pos()
        self._start_ripple()
        scene = self.scene()

        if self.slider_values and not (self.slider_handle and self.slider_handle.contains(event.pos())):
            if not self.incremental_value:
                self._is_dragging = True
                self._drag_button = event.button()
                self._update_slider_value(event.pos())
        elif not self.slider_values:
            value = None
            if event.button() == Qt.MouseButton.LeftButton:
                if self.toggle_values:
                    self._toggle_state()
                    value = self._toggle_value
                if self.callbackL:
                    if value is not None and len(inspect.signature(self.callbackL).parameters) > 0:
                        self.callbackL(value)
                    else:
                        self.callbackL()
                if self.auto_close and scene and hasattr(scene, 'hide_radial_menu'):
                    scene.hide_radial_menu()
            elif event.button() == Qt.MouseButton.RightButton:
                if self.toggle_values:
                    value = self._toggle_value
                if self.callbackR:
                    if value is not None and len(inspect.signature(self.callbackR).parameters) > 0:
                        self.callbackR(value)
                    else:
                        self.callbackR()
            elif event.button() == Qt.MouseButton.MiddleButton:
                if self.toggle_values:
                    value = self._toggle_value
                if self.callbackM:
                    if value is not None and len(inspect.signature(self.callbackM).parameters) > 0:
                        self.callbackM(value)
                    else:
                        self.callbackM()

        if self.isUnderMouse():
            self.itemColor = self.hover_color
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.editable:
            return
        if self._is_dragging and self.slider_values and not self.incremental_value:
            self._update_slider_value(event.pos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.editable:
            return
        if self._is_dragging:
            self._is_dragging = False
            self._drag_button = None
            self.update()
        super().mouseReleaseEvent(event)

    def _update_slider_value(self, pos):
        if not self.editable or not self.slider_values:
            return
        min_val, max_val, _ = self.slider_values
        if self.incremental_value:
            desired_x = pos.x() - self.slider_handle.drag_offset
            left_limit = self._bounding.left() + self.handle_r
            right_limit = self._bounding.right() - self.handle_r
            clamped_x = max(left_limit, min(desired_x, right_limit))
            self.slider_handle.setPos(QPointF(clamped_x, self._bounding.center().y()))
            self.current_offset = desired_x - self.center_x
        else:
            relative_x = pos.x() - self._bounding.left()
            progress_ratio = relative_x / self._bounding.width()
            progress_ratio = max(0.0, min(1.0, progress_ratio))
            self._slider_value = min_val + progress_ratio * (max_val - min_val)
            self._update_handle_position()
            self._update_additional_text()
            if self._drag_button == Qt.MouseButton.LeftButton and self.callbackL:
                if len(inspect.signature(self.callbackL).parameters) > 0:
                    self.callbackL(self._slider_value)
                else:
                    self.callbackL()
            elif self._drag_button == Qt.MouseButton.RightButton and self.callbackR:
                if len(inspect.signature(self.callbackR).parameters) > 0:
                    self.callbackR(self._slider_value)
                else:
                    self.callbackR()
            elif self._drag_button == Qt.MouseButton.MiddleButton and self.callbackM:
                if len(inspect.signature(self.callbackM).parameters) > 0:
                    self.callbackM(self._slider_value)
                else:
                    self.callbackM()
            self.update()

    def _increment_value(self):
        if not self._is_dragging or not self.slider_values:
            return
        min_val, max_val, _ = self.slider_values
        half_width = self._bounding.width() / 2
        normalized = self.current_offset / half_width
        delta = normalized * (max_val - min_val) * (self.incremental_value/(max_val*100))
        new_value = max(min_val, min(max_val, self._slider_value + delta))
        if new_value != self._slider_value:
            self._slider_value = new_value
            self._update_additional_text()
            self.update()
            if self._drag_button == Qt.MouseButton.LeftButton and self.callbackL:
                if len(inspect.signature(self.callbackL).parameters) > 0:
                    self.callbackL(self._slider_value)
                else:
                    self.callbackL()
            elif self._drag_button == Qt.MouseButton.RightButton and self.callbackR:
                if len(inspect.signature(self.callbackR).parameters) > 0:
                    self.callbackR(self._slider_value)
                else:
                    self.callbackR()
            elif self._drag_button == Qt.MouseButton.MiddleButton and self.callbackM:
                if len(inspect.signature(self.callbackM).parameters) > 0:
                    self.callbackM(self._slider_value)
                else:
                    self.callbackM()

    def _snap_handle_to_center(self):
        self.slider_handle.setPos(QPointF(self.center_x, self._bounding.center().y()))
        self.current_offset = 0.0
        self.update()

    def _update_handle_position(self):
        if not self.slider_handle or not self.slider_values:
            return
        min_val, max_val, _ = self.slider_values
        progress_ratio = (self._slider_value - min_val) / (max_val - min_val)
        handle_x = self.center_x if self.incremental_value else self._bounding.left() + progress_ratio * self._bounding.width()
        self.slider_handle.setPos(QPointF(handle_x, self._bounding.center().y()))

    def _update_additional_text(self):
        if self.additional_text_item and (self.slider_values or self.toggle_values):
            base = self.additional_text if self.additional_text else ""
            if self.show_value:
                if self.slider_values:
                    percent = "%" if self.progress_bar else ""
                    value_str = f" {int(round(self._slider_value))}{percent}"
                elif self.toggle_values:
                    min_val, max_val, _ = self.toggle_values
                    if min_val == 0 and max_val == 1:
                        value_str = f"   {'On' if self._toggle_value else 'Off'}"
                    else:
                        value_str = f" {self._toggle_value}"
                else:
                    value_str = ""
            else:
                value_str = ""
            new_text = base + value_str
            self.additional_text_item.setHtml(new_text)
            add_bounding = self.additional_text_item.boundingRect()
            main_bounding = self.main_symbol_item.boundingRect()
            main_right = main_bounding.width() / 2
            padding = 3
            add_left = main_right + padding
            self.additional_text_item.setPos(add_left, -add_bounding.height() / 2)

    def _start_ripple(self):
        if not self.editable:
            return
        if self.ripple_anim_group:
            self.ripple_anim_group.stop()
        self.ripple_anim_group = QParallelAnimationGroup()

        radius_anim = QPropertyAnimation(self, b"ripple_radius")
        radius_anim.setDuration(400)
        radius_anim.setStartValue(0.0)
        radius_anim.setEndValue(self.ripple_end_radius)
        radius_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        opacity_anim = QPropertyAnimation(self, b"ripple_opacity")
        opacity_anim.setDuration(400)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.ripple_anim_group.addAnimation(radius_anim)
        self.ripple_anim_group.addAnimation(opacity_anim)
        self.ripple_anim_group.finished.connect(self._reset_ripple)
        self.ripple_anim_group.start()

    def _reset_ripple(self):
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self.update()
        if not self.isUnderMouse():
            self.color_anim = QPropertyAnimation(self, b"itemColor")
            self.color_anim.setDuration(250)
            self.color_anim.setStartValue(self.itemColor)
            self.color_anim.setEndValue(self.normal_color)
            self.color_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.color_anim.start()