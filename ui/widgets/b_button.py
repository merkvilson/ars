from PyQt6.QtWidgets import (
    QGraphicsTextItem,
    QGraphicsObject,
    QGraphicsRectItem,
    QGraphicsItem,
    QGraphicsProxyWidget, 
    QWidget,
    QLineEdit,
    QGraphicsColorizeEffect,)

from PyQt6.QtSvgWidgets import QGraphicsSvgItem

from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QPainterPath,
    QPixmap,
    QImageReader,)

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
from typing import Optional, Callable, Tuple, Any, Union, List


import inspect
import time
from theme.fonts.new_fonts import get_font
from theme import colors
from .widget_control import set_updated_config
from core.cursor_modifier import CursorModifier

from core.sound_manager import play_sound


class SliderHandle(QGraphicsRectItem):
    """Invisible handle overlay for slider interaction.
    
    Captures mouse events for slider dragging and provides:
    - Left-click drag: Update slider value
    - Right-click: Open inline edit field (if no callbackR defined)
    - Short left-click (<0.15s): Open inline edit field
    
    Args:
        parent: The parent BButton instance.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_button = parent
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)
        self._is_dragging = False
        self._drag_button = None
        self.is_incremental = parent.incremental_value
        self.initial_click_x = 0.0
        self._press_timestamp = 0.0

    def mousePressEvent(self, event):
        if self.parent_button.slider_values and self.parent_button.editable:
            if (event.button() == Qt.MouseButton.RightButton and 
                self.parent_button.use_extended_shape and 
                self.parent_button.config.callbackR is None):
                
                QTimer.singleShot(0, self.parent_button._open_edit_field)
                event.accept()
                return

            self._is_dragging = True
            self._drag_button = event.button()
            self.parent_button._is_dragging = True
            self.parent_button._drag_button = self._drag_button
            self.initial_click_x = event.pos().x()
            self.grabMouse()
            if event.button() == Qt.MouseButton.LeftButton:
                self._press_timestamp = time.time()
                if self.is_incremental:
                    self.parent_button._initial_slider_value = self.parent_button._slider_value
                else:
                    self.parent_button._update_slider_value(self.mapToParent(event.pos()))
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.parent_button.slider_values and self.parent_button.editable:
            self.parent_button.ripple_center = self.mapToParent(event.pos())
            self.parent_button._start_ripple()
            self.ungrabMouse()

            if event.button() == Qt.MouseButton.LeftButton:
                if time.time() - self._press_timestamp < 0.15:
                    QTimer.singleShot(0, self.parent_button._open_edit_field)
            else:
                self.parent_button._trigger_callback()

            self._is_dragging = False
            self._drag_button = None
            self.parent_button._is_dragging = False
            self.parent_button._drag_button = None
            
            # Start revert timer after button release
            self.parent_button._start_revert_timer()

            event.accept()


    def mouseMoveEvent(self, event):
        if self._is_dragging and self.parent_button.slider_values and self.parent_button.editable:
            if self._drag_button == Qt.MouseButton.LeftButton:
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


class EditField(QLineEdit):
    """Inline text input field for editing slider or text_value values.
    
    A transparent QLineEdit that appears over the button's additional text area.
    Handles keyboard events (Escape to cancel, Enter to commit) and focus loss.
    
    Args:
        b_button: The parent BButton instance.
    """
    def __init__(self, b_button):
        super().__init__()
        self.b_button = b_button
        # Prevent context menu from appearing
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.b_button._cancel_edit_value()
        else:
            super().keyPressEvent(event)
            
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # We rely on editingFinished which is emitted on focus loss too.
        # But sometimes it's safer to trigger commit here if editingFinished doesn't fire.
        # However, editingFinished usually fires.
        # To be safe against double calls, _commit_edit_value checks for edit_proxy existence.
        self.b_button._commit_edit_value()

    def mouseReleaseEvent(self, event):
        # Consume Right Click Release to prevent any default behavior (like context menu triggers)
        # that might cause focus loss.
        if event.button() == Qt.MouseButton.RightButton:
            event.accept()
            return
        super().mouseReleaseEvent(event)

@dataclass
class BButtonConfig:
    """Configuration dataclass for BButton properties."""
    symbol: str = ""
    radius: int = 22
    color: QColor = field(default_factory=lambda: colors.button_color)
    hover_color: QColor = field(default_factory=lambda: colors.hover_color)
    symbol_color: QColor = field(default_factory=lambda: colors.symbol_color)
    additional_text_color: QColor = field(default_factory=lambda: colors.additional_text_color)
    hotkey_text_color: QColor = field(default_factory=lambda: colors.hotkey_text_color)
    font: QFont = field(default_factory=lambda: get_font(16))
    additional_font: QFont = field(default_factory=lambda: QFont("Arial", 10))
    hover_scale: float = 1.0
    callbackL: Optional[Callable] = None
    callbackR: Optional[Callable] = None
    callbackM: Optional[Callable] = None
    callback_hover_in: Optional[Callable] = None
    callback_hover_out: Optional[Callable] = None
    additional_text: Optional[str] = None
    hotkey_text: Optional[str] = None
    use_extended_shape: bool = False
    auto_close: bool = False
    slider_values: Optional[Union[Tuple[int, int, int], List[int]]] = None
    slider_color: QColor = field(default_factory=lambda: colors.slider_color)
    toggle_values: Optional[Any] = None
    toggle_color: QColor = field(default_factory=lambda: colors.toggle_color)
    toggle_hover_color: QColor = field(default_factory=lambda: colors.toggle_hover_color)
    toggle_disabled_color: QColor = field(default_factory=lambda: colors.toggle_disabled_color)
    toggle_disabled_hover_color: QColor = field(default_factory=lambda: colors.toggle_disabled_hover_color)
    show_value: bool = False
    show_symbol: bool = True
    editable: bool = True
    progress_bar: bool = False
    image_path: Optional[str] = None
    clip_to_shape: bool = True
    incremental_value: bool | tuple = False
    inner_widget: Optional[QWidget] = None
    text_value: Optional[str] = None


class BButton(QGraphicsObject):
    """Versatile bubble button widget for the ARS floating UI system.
    
    Supports multiple modes:
    - **Basic Button**: Simple clickable button with icon and optional label.
    - **Slider Mode**: Horizontal slider with drag/click interaction (slider_values).
    - **Toggle Mode**: On/off or multi-state toggle (toggle_values).
    - **Text Input Mode**: Editable text field (text_value).
    - **Progress Bar**: Non-interactive progress display (progress_bar).
    
    Interaction:
    - Left-click: Primary action / toggle state / open text edit (for text_value).
    - Right-click: Secondary action / open edit field (sliders without callbackR).
    - Middle-click: Revert to default value.
    - Short left-click (<0.15s) on slider: Open edit field.
    - Scroll wheel: Increment/decrement slider value.
    
    Visual Features:
    - Ripple animation on click.
    - Hover color/scale animation.
    - Hotkey badge display.
    - Image background support.
    - Embedded inner widgets.
    
    Args:
        config: BButtonConfig instance with all button properties.
    
    Example:
        >>> config = BButtonConfig(
        ...     symbol="",
        ...     additional_text="Volume",
        ...     slider_values=(0, 100, 50),
        ...     show_value=True,
        ...     use_extended_shape=True,
        ...     callbackL=lambda v: print(f"Volume: {v}")
        ... )
        >>> button = BButton(config)
    """
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
        self.toggle_disabled_color = config.toggle_disabled_color
        self.toggle_disabled_hover_color = config.toggle_disabled_hover_color
        self.show_value = config.show_value
        self.show_symbol = config.show_symbol
        self.editable = config.editable
        self.progress_bar = config.progress_bar
        self.incremental_value = config.incremental_value if isinstance(config.incremental_value, (int,bool)) else config.incremental_value[0] 
        self.text_value = config.text_value

        if self.text_value is not None:
            self.show_value = True
        
        # Timer for reverting symbol back after showing value
        self._original_symbol = self.symbol
        self._revert_timer = None

        # Hide symbol if text is too long (but not for SVG paths)
        if len(self.symbol) > 2 and not self.symbol.lower().endswith('.svg'):
            self.show_symbol = False
        
        self.image_path = config.image_path  
        self.pixmap = None 
        if self.image_path:
            if self.image_path.lower().endswith(('.tif', '.tiff')):
                reader = QImageReader(self.image_path)
                count = reader.imageCount()
                if count > 0:
                    reader.jumpToImage(count - 1)
                    image = reader.read()
                    if not image.isNull():
                        self.pixmap = QPixmap.fromImage(image)

            if self.pixmap is None:
                self.pixmap = QPixmap(self.image_path) 

            if self.pixmap.isNull():
                self.pixmap = None
                print(f"Warning: Failed to load image from '{self.image_path}'") 


        if self.progress_bar:
            self.slider_values = (0, 100, 0, 0)
            self._slider_value = 0
            self.slider_color = colors.slider_progress_color
            self.editable = False
        self._is_dragging = False
        self._drag_button = None
        self.slider_handle = None
        self.radio_group = None
        
        # Handle slider_values with safety check
        if isinstance(config.slider_values, (tuple, list)) and len(config.slider_values) >= 3:
            vals = list(config.slider_values)
            if len(vals) == 3:
                vals.append(vals[2])  # Default is current if not provided
            self.slider_values = tuple(vals[:4])
            self._slider_value = self.slider_values[2]
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
            width =  (8 * self.radius)
            if isinstance(self.use_extended_shape, tuple):
                if self.use_extended_shape[0]: width = (self.use_extended_shape[0] * self.radius) * 2
                else: width = 8 * self.radius
                if self.use_extended_shape[1]: height = (self.use_extended_shape[1] * self.radius) * 2
                else: height = 2 * self.radius

            self._bounding = QRectF( -self.radius,  -self.radius, width, height)
        else:
            self._bounding = QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)


        self.normal_color = config.color
        self.hover_color = config.hover_color
        if self.slider_values:
            normal_alpha = int(self.normal_color.alpha() * 0.7)
            hover_alpha = int(self.hover_color.alpha() * 0.7)
            self.normal_color = QColor(self.normal_color.red(), self.normal_color.green(), self.normal_color.blue(), normal_alpha)
            self.hover_color = QColor(self.hover_color.red(), self.hover_color.green(), self.hover_color.blue(), hover_alpha)
        
        # Darken colors if not editable
        if not self.editable:
            self.normal_color = self.normal_color.darker(150)
            self.hover_color = self.normal_color
        
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


        self.original_scale = 0.9 if not self.use_extended_shape else 0.96
        self.hover_scale = float(config.hover_scale)
        self.setScale(self.original_scale)
        self.setOpacity(1.0)

        self.setTransformOriginPoint(self.boundingRect().center())

        # Main Symbol (text or SVG)
        self._is_svg_symbol = isinstance(self.symbol, str) and self.symbol.lower().endswith('.svg')
        self._symbol_color = config.symbol_color
        if not self.editable:
            self._symbol_color = self._symbol_color.darker(150)
        if not self.show_symbol:
            self._symbol_color = QColor(self._symbol_color.red(), self._symbol_color.green(), self._symbol_color.blue(), 0)
        self._font = config.font
        
        if self._is_svg_symbol:
            self.main_symbol_item = QGraphicsSvgItem(self.symbol, self)
            # Apply colorize effect to tint SVG with symbol color
            self._svg_colorize = QGraphicsColorizeEffect()
            self._svg_colorize.setColor(self._symbol_color)
            self._svg_colorize.setStrength(1.0)
            self.main_symbol_item.setGraphicsEffect(self._svg_colorize)
            # Scale SVG to fit within radius
            svg_bounds = self.main_symbol_item.boundingRect()
            if svg_bounds.width() > 0 and svg_bounds.height() > 0:
                target_size = self.radius * 1.5
                scale_factor = min(target_size / svg_bounds.width(), target_size / svg_bounds.height())
                self.main_symbol_item.setScale(scale_factor)
                scaled_width = svg_bounds.width() * scale_factor
                scaled_height = svg_bounds.height() * scale_factor
                self.main_symbol_item.setPos(-scaled_width / 2, -scaled_height / 2)
            if not self.show_symbol:
                self.main_symbol_item.setOpacity(0)
            elif not self.editable:
                self.main_symbol_item.setOpacity(0.5)
            bounding = QRectF(-self.radius * 0.75, -self.radius * 0.75, self.radius * 1.5, self.radius * 1.5)
        else:
            self.main_symbol_item = QGraphicsTextItem(self.symbol, self)
            self.main_symbol_item.setDefaultTextColor(self._symbol_color)
            self.main_symbol_item.setFont(self._font)
            bounding = self.main_symbol_item.boundingRect()
            self.main_symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)

        # Additional Text (including slider/toggle value if applicable)
        initial_base = self.additional_text if self.additional_text else ""
        initial_text = initial_base
        
        self._additional_text_color = config.additional_text_color
        if not self.editable:
            self._additional_text_color = self._additional_text_color.darker(150)

        if self.show_value:
            if self.slider_values:
                initial_value = f" {int(round(self._slider_value))}{"%" if self.progress_bar else ""}"
                initial_text = initial_base + initial_value
            elif self.toggle_values:
                min_val, max_val, _ = self.toggle_values
                if min_val == 0 and max_val == 1:
                    initial_value = f"   {'On' if self._toggle_value else 'Off'}"
                else:
                    initial_value = f" {self._toggle_value}"
                initial_text = initial_base + initial_value
            elif self.text_value is not None:
                if self.text_value == "":
                    initial_text = initial_base
                    self._additional_text_color = self._additional_text_color.darker(150)
                else:
                    initial_text = self.text_value

        if initial_text:
            self.additional_text_item = QGraphicsTextItem(self)
            self._additional_font = config.additional_font
            self.additional_text_item.setFont(self._additional_font)
            self.additional_text_item.setDefaultTextColor(self._additional_text_color)
            self.additional_text_item.setHtml(initial_text)
            add_bounding = self.additional_text_item.boundingRect()
            main_right = bounding.width() / 2
            padding = 3 if self.show_symbol else -25
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
            self._initial_slider_value = self._slider_value

            self.slider_handle.setRect(QRectF(-9999/2, -50/2, 9999, 50))

            if self.incremental_value: 
                self._cursor_modifier = CursorModifier(
                    trigger_widget=self.slider_handle,
                    axis="x" if isinstance(self.config.incremental_value, (int, bool)) else self.config.incremental_value[1],
                    target = None,
                    cursor_type=("invisible"),
                    anchor="center",
                    teleport_back=True,
                    infinite_movement=True)



        # Ripple effect
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self.ripple_center = self.boundingRect().center()
        self.ripple_end_radius = max(self._bounding.width(), self._bounding.height()) / 2 * 1.5
        self.ripple_anim_group = None


        # Inner Widget (behind slider)
        self.inner_widget_proxy = None
        if config.inner_widget:
            self.inner_widget_proxy = QGraphicsProxyWidget(self)
            self.inner_widget_proxy.setWidget(config.inner_widget)
            # Position it to fill the button's bounds
            widget_rect = self._bounding
            self.inner_widget_proxy.setPos(widget_rect.topLeft())
            self.inner_widget_proxy.resize(widget_rect.size())
            self.inner_widget_proxy.setZValue(-0.5)  # Behind slider (which is at 1.0) but in front of background


        # Default callbacks
        def default_callbackL(value=None):
            action = "clicked" if value is None else f"set to {value}"
            print(f"{self.symbol} {action}")

        def default_callbackR(value=None):
            action = "right-clicked" if value is None else f"set to {value}"
            print(f"{self.symbol} {action}")
        
        def default_callbackM(value=None):
            # Revert slider or toggle to default value
            play_sound("click")
            if self.slider_values:
                if len(self.slider_values) >= 4:
                    default_val = self.slider_values[3]
                else:
                    default_val = self.slider_values[2]
                self._slider_value = default_val
                self._update_additional_text()
                
                # Temporarily show value in symbol for small/incremental sliders (text only)
                if not self.use_extended_shape and not self._is_svg_symbol:
                    value_txt = str(int(round(self._slider_value)))
                    self.main_symbol_item.setPlainText(value_txt)
                    self.main_symbol_item.setFont(QFont("Arial", 18 - len(value_txt), QFont.Weight.Bold))
                    bounding = self.main_symbol_item.boundingRect()
                    self.main_symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)
                    self._start_revert_timer()
                
                self.update()
                # Execute callbackL after reverting
                if self.callbackL:
                    if len(inspect.signature(self.callbackL).parameters) > 0:
                        self.callbackL(self._slider_value)
                    else:
                        self.callbackL()
            elif self.toggle_values:
                _, _, default_val = self.toggle_values
                self._toggle_value = default_val
                self._update_additional_text()
                self._update_colors()
                self._refresh_color()
                self.update()
                # Execute callbackL after reverting
                if self.callbackL:
                    if len(inspect.signature(self.callbackL).parameters) > 0:
                        self.callbackL(self._toggle_value)
                    else:
                        self.callbackL()
            elif self.text_value is not None:
                self.text_value = self.config.text_value
                self._update_additional_text()
                self._update_colors()
                self.update()
                if self.callbackL:
                    if len(inspect.signature(self.callbackL).parameters) > 0:
                        self.callbackL(self.text_value)
                    else:
                        self.callbackL()
            else:
                print(f"{self.symbol} middle-clicked (no value to revert)")

        self.callbackL = config.callbackL if config.callbackL else default_callbackL
        self.callbackR = config.callbackR if config.callbackR else default_callbackR
        self.callbackM = config.callbackM if config.callbackM else default_callbackM

    def _create_hotkey_items(self):
        """Create hotkey badge text items with rounded outline backgrounds."""
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
      
        current_left = right_edge - 30

        for word in words:
            text_item = QGraphicsTextItem(self)
            # text_item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            text_item.setFont(get_font(font_name="JetBrainsMono-Bold.ttf", size=13, weight=QFont.Weight.Bold))
            text_item.setDefaultTextColor(self._hotkey_text_color)
            text_item.setPlainText(word)
            bounding = text_item.boundingRect()
            text_item.setPos(current_left, -bounding.height() / 2)
            self.hotkey_text_items.append(text_item)

            outline_item = RoundedRectOutline(corner_radius=4, parent=self)
            outline_padding = 1
            outline_rect = QRectF(
                current_left - outline_padding,
                -bounding.height() / 2 - outline_padding + 4,
                bounding.width() + 2 * outline_padding,
                bounding.height() + 2 * outline_padding - 8
            )
            outline_item.setRect(outline_rect)
            outline_item.setPen(QPen(self._hotkey_text_color, 2))
            # Set background to match the button's current brush
            outline_item.setBrush(self.current_brush)
            outline_item.setZValue(-1)
            self.hotkey_outline_items.append(outline_item)

            current_left += bounding.width() + space_between

    def _update_colors(self):
        """Recalculate normal_color and hover_color based on current state.
        
        Applies color adjustments for:
        - Toggle on/off states
        - Slider transparency
        - Text value darkening (no hover effect)
        """
        if self.toggle_values and self._toggle_value > 0:
            self.normal_color = self.toggle_color
            self.hover_color = self.toggle_hover_color
        elif self.toggle_values and self._toggle_value == 0:
            self.normal_color = self.toggle_disabled_color
            self.hover_color = self.toggle_disabled_hover_color
        else:
            self.normal_color = self.config.color
            self.hover_color = self.config.hover_color
        if self.slider_values:
            normal_alpha = int(self.normal_color.alpha() * 0.7)
            hover_alpha = int(self.hover_color.alpha() * 0.7)
            self.normal_color = QColor(self.normal_color.red(), self.normal_color.green(), self.normal_color.blue(), normal_alpha)
            self.hover_color = QColor(self.hover_color.red(), self.hover_color.green(), self.hover_color.blue(), hover_alpha)
        
        if self.text_value is not None:
            self.hover_color = self.normal_color.darker(200)
            self.normal_color = self.normal_color.darker(250)

    def _refresh_color(self):
        """Apply the appropriate color based on hover/editable state."""
        if hasattr(self, 'color_anim') and self.color_anim and self.color_anim.state() == QPropertyAnimation.State.Running:
            self.color_anim.stop()
        if not self.editable:
            self.itemColor = self.normal_color
        elif self.scale() == self.hover_scale:
            self.itemColor = self.hover_color
        else:
            self.itemColor = self.normal_color

    def _open_edit_field(self):
        """Create and display an inline text edit field.
        
        Opens a transparent QLineEdit overlay for manual value entry.
        For sliders: displays current numeric value, commits on Enter/focus loss.
        For text_value: displays current text, updates on commit.
        Press Escape to cancel without saving.
        """
        if hasattr(self, 'edit_proxy') and self.edit_proxy:
            return

        if not self.additional_text_item:
            return

        self.edit_field = EditField(self)
        
        if self.text_value is not None:
            text = self.text_value
        else:
            val = self._slider_value
            if isinstance(val, float):
                text = f"{val:.2f}".rstrip('0').rstrip('.')
            else:
                text = str(val)
            
        self.edit_field.setText(text)
        self.edit_field.selectAll()
        
        font = self._additional_font
        color = self._additional_text_color
        self.edit_field.setFont(font)
        self.edit_field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; 
                color: {color.name()}; 
                border: none;
                padding: 0px;
                selection-background-color: #808080;
                selection-color: white;
            }}
        """)
        
        self.edit_proxy = QGraphicsProxyWidget(self)
        self.edit_proxy.setWidget(self.edit_field)
        self.edit_proxy.setZValue(1000) # Ensure it's on top
        
        if self.additional_text_item:
            self.additional_text_item.setVisible(False)
            pos = self.additional_text_item.pos()
            available_width = self._bounding.right() - pos.x() - 10
            if available_width < 50: available_width = 50
            
            self.edit_field.setFixedWidth(int(available_width))
            self.edit_field.setFixedHeight(int(self.additional_text_item.boundingRect().height()) + 4)
            
            self.edit_proxy.setPos(pos.x(), -self.edit_field.height() / 2)
        else:
            self.edit_proxy.setPos(0, -10)
            self.edit_field.setFixedWidth(50)

        self.edit_field.editingFinished.connect(self._commit_edit_value)
        self.edit_field.setFocus()

    def _commit_edit_value(self):
        """Schedule deferred commit of the edit field value.
        
        Uses QTimer.singleShot(0) to safely clean up the edit field
        without crashing when called from within an event handler.
        """
        QTimer.singleShot(0, self._commit_edit_value_deferred)

    def _commit_edit_value_deferred(self):
        """Apply the edited value and close the edit field.
        
        For sliders: parses numeric input, clamps to min/max, triggers callback.
        For text_value: updates the text directly, triggers callback.
        Invalid numeric input is silently ignored.
        """
        if not hasattr(self, 'edit_proxy') or not self.edit_proxy:
            return
            
        text = self.edit_field.text()
        
        if self.text_value is not None:
            self.text_value = text
            self._update_additional_text()
            if self.callbackL:
                 if len(inspect.signature(self.callbackL).parameters) > 0:
                    self.callbackL(self.text_value)
                 else:
                    self.callbackL()
            self._cancel_edit_value()
            return

        try:
            if '.' in text:
                new_val = float(text)
            else:
                new_val = int(text)
                
            min_val, max_val = self.slider_values[:2]
            new_val = max(min_val, min(max_val, new_val))
            
            self._slider_value = new_val
            self._update_additional_text()
            
            if self.callbackL:
                 if len(inspect.signature(self.callbackL).parameters) > 0:
                    self.callbackL(self._slider_value)
                 else:
                    self.callbackL()
                    
        except ValueError:
            pass 
            
        self._cancel_edit_value()

    def _cancel_edit_value(self):
        """Close the edit field without saving changes."""
        if hasattr(self, 'edit_proxy') and self.edit_proxy:
            self.edit_proxy.setVisible(False)
            self.edit_proxy.setParentItem(None)
            self.edit_proxy.deleteLater()
            self.edit_proxy = None
            
        self.edit_field = None
            
        if self.additional_text_item:
            self.additional_text_item.setVisible(True)

    def _toggle_state(self):
        """Cycle the toggle value and update visuals.
        
        For radio groups: turns on this button and turns off others.
        For regular toggles: cycles through min to max values.
        """
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
            min_val, max_val = self.slider_values[:2]
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
        if not self.editable:return

        play_sound("hover")
        if self.config.callback_hover_in:
            self.config.callback_hover_in()
        self.itemColor = self.hover_color
        self.setScale(self.hover_scale)
        if self.additional_text_item:
            bold_font = QFont(self._additional_font)
            bold_font.setWeight(QFont.Weight.Bold)
            self.additional_text_item.setFont(bold_font)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.editable:return

        if self.config.callback_hover_out:
            self.config.callback_hover_out()
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
            if (event.button() == Qt.MouseButton.RightButton and 
                self.use_extended_shape and 
                self.config.callbackR is None):
                
                self._open_edit_field()
                event.accept()
                return

            if not self.incremental_value:
                self._is_dragging = True
                self._drag_button = event.button()
                self._update_slider_value(event.pos())
        elif not self.slider_values:
            value = None
            if event.button() == Qt.MouseButton.LeftButton:
                if self.text_value is not None:
                    QTimer.singleShot(0, self._open_edit_field)
                    return

                if self.toggle_values:
                    self._toggle_state()
                    value = self._toggle_value
                if self.callbackL:
                    if len(inspect.signature(self.callbackL).parameters) > 0:
                        self.callbackL(value)
                    else:
                        self.callbackL()
                # if self.auto_close and scene and hasattr(scene, 'hide_radial_menu'):
                #     scene.hide_radial_menu()
            elif event.button() == Qt.MouseButton.RightButton:
                if self.toggle_values:
                    value = self._toggle_value
                if self.callbackR:
                    if len(inspect.signature(self.callbackR).parameters) > 0:
                        self.callbackR(value)
                    else:
                        self.callbackR()
            elif event.button() == Qt.MouseButton.MiddleButton:
                if self.toggle_values:
                    value = self._toggle_value
                if self.callbackM:
                    if len(inspect.signature(self.callbackM).parameters) > 0:
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
            
            # Start revert timer after button release
            self._start_revert_timer()

            self.update()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        
        if self.editable and self.slider_values:
            step = self.incremental_value if self.incremental_value else 1
            
            delta = 0
            if hasattr(event, 'delta'):
                delta = event.delta()
            elif hasattr(event, 'angleDelta'):
                delta = event.angleDelta().y()
            
            if delta == 0:
                return

            if delta < 0:
                step = -step
            
            min_val, max_val = self.slider_values[:2]
            new_value = self._slider_value + step
            self._slider_value = max(min_val, min(max_val, new_value))
            
            self._update_additional_text()
            
            if self.callbackL:
                if len(inspect.signature(self.callbackL).parameters) > 0:
                    self.callbackL(self._slider_value)
                    play_sound("click")
                else:
                    self.callbackL()
            
            if not self.use_extended_shape and not self._is_svg_symbol:
                value_txt = str(int(round(self._slider_value)))
                self.main_symbol_item.setPlainText(value_txt)
                self.main_symbol_item.setFont(QFont("Arial", 16 - len(value_txt), QFont.Weight.Bold))
                bounding = self.main_symbol_item.boundingRect()
                self.main_symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)
                self._start_revert_timer()

            self.update()
            event.accept()
        else:
            super().wheelEvent(event)

    def _update_slider_value(self, pos):
        """Calculate and apply new slider value from position or cursor offset.
        
        For incremental mode: uses accumulated cursor offset from CursorModifier.
        For direct mode: calculates value from click/drag position ratio.
        
        Args:
            pos: Mouse position in parent coordinates.
        """
        if not (self.editable and self.slider_values):
            return
        min_val, max_val = self.slider_values[:2]
        if self.incremental_value: # Calculate new value using cursor offset
            current_offset = self._cursor_modifier.get_accumulated_offset()
            
            # Determine which axis to use based on modifier configuration
            axis = self._cursor_modifier.axis
            if axis == 'y':
                distance = current_offset.y()
            else:
                distance = current_offset.x()

            delta = distance * (self.incremental_value / 100)
            new_value = self._initial_slider_value + delta

            # Clamp the internal cursor modifier value to prevent drift
            if new_value < min_val or new_value > max_val:
                clamped_val = max(min_val, min(max_val, new_value))
                factor = (self.incremental_value / 100)
                if factor != 0:
                    new_distance = (clamped_val - self._initial_slider_value) / factor
                    
                    if axis == 'y':
                        current_offset.setY(int(new_distance))
                    else:
                        current_offset.setX(int(new_distance))
                        
                    self._cursor_modifier.set_accumulated_offset(current_offset)
                new_value = clamped_val
        else: # Calculate new value based on position ratio
            relative_x = pos.x() - self._bounding.left()
            progress_ratio = relative_x / self._bounding.width()
            progress_ratio = max(0.0, min(1.0, progress_ratio))
            new_value = min_val + progress_ratio * (max_val - min_val)
        self._slider_value = max(min_val, min(max_val, new_value))    # Clamp and assign the final value
        self._update_additional_text()
        self._trigger_callback()
        
        # Temporarily show value in symbol if incremental_value is active (text only)
        if self.incremental_value and not self.use_extended_shape and not self._is_svg_symbol:
            value_txt = str(int(round(self._slider_value)))
            self.main_symbol_item.setPlainText(value_txt)
            self.main_symbol_item.setFont(QFont("Arial", 16 - len(value_txt), QFont.Weight.Bold))
            bounding = self.main_symbol_item.boundingRect()
            self.main_symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)
            
            # Stop any existing timer but don't start a new one while dragging
            if self._revert_timer:
                self._revert_timer.stop()
        
        self.update()    # Update visuals and trigger related logic

    def _trigger_callback(self):
        """Invoke the appropriate callback based on which mouse button is being dragged."""
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

    def _revert_symbol(self):
        """Revert the symbol back to its original text after showing the value."""
        if self._is_svg_symbol:
            return  # SVG symbols don't need reverting
        if not self._original_symbol.replace('.', '', 1).replace('-', '', 1).isdigit():
            self.main_symbol_item.setPlainText(self._original_symbol)
            self.main_symbol_item.setFont(self._font)
            bounding = self.main_symbol_item.boundingRect()
            self.main_symbol_item.setPos(-bounding.width() / 2, -bounding.height() / 2)
            self.update()

    def _start_revert_timer(self):
        """Start the timer to revert symbol after button release."""
        if not self.use_extended_shape:
            if self._revert_timer:
                self._revert_timer.stop()
            self._revert_timer = QTimer()
            self._revert_timer.setSingleShot(True)
            self._revert_timer.timeout.connect(self._revert_symbol)
            self._revert_timer.start(1000)


    def _update_additional_text(self):
        """Update the displayed text based on current value.
        
        Handles display logic for:
        - Sliders: "Label Value" or "Label Value%" (progress bar)
        - Toggles: "Label On/Off" or "Label N" (multi-state)
        - Text value: Shows text_value, or additional_text as placeholder if empty
        
        Empty text_value displays additional_text in darker color as placeholder.
        """
        if self.additional_text_item and (self.slider_values or self.toggle_values or self.text_value is not None):
            base = self.additional_text if self.additional_text else ""
            new_text = base
            
            text_color = self.config.additional_text_color
            if not self.editable:
                text_color = text_color.darker(150)

            if self.show_value:
                if self.slider_values:
                    percent = "%" if self.progress_bar else ""
                    value_str = f" {int(round(self._slider_value))}{percent}"
                    new_text = base + value_str
                elif self.toggle_values:
                    min_val, max_val, _ = self.toggle_values
                    if min_val == 0 and max_val == 1:
                        value_str = f"   {'On' if self._toggle_value else 'Off'}"
                    else:
                        value_str = f" {self._toggle_value}"
                    new_text = base + value_str
                elif self.text_value is not None:
                    if self.text_value == "":
                        new_text = base
                        text_color = text_color.darker(150)
                    else:
                        new_text = self.text_value

            self.additional_text_item.setDefaultTextColor(text_color)
            self.additional_text_item.setHtml(new_text)
            add_bounding = self.additional_text_item.boundingRect()
            main_bounding = self.main_symbol_item.boundingRect()
            main_right = main_bounding.width() / 2
            padding = 3
            add_left = main_right + padding
            self.additional_text_item.setPos(add_left, -add_bounding.height() / 2)

    def _start_ripple(self):
        """Start the ripple click animation from the current ripple_center."""
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
        """Reset ripple state and animate color back to normal if not hovering."""
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