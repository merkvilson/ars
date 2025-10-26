from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
import numpy as np
import theme.fonts.new_fonts as RRRFONT
from vispy.color import Color as VispyColor
from PyQt6.QtWidgets import QWidget, QSlider, QHBoxLayout, QLabel, QStyleOptionSlider, QStyle
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPen
from PyQt6.QtCore import Qt, QRectF
from core.sound_manager import play_sound
from PyQt6.QtWidgets import QFileDialog

from PyQt6.QtGui import QCursor, QColor
from PyQt6.QtCore import QPoint

from ars_cmds.util_cmds.color_convert import rgb_to_hsv, hsv_to_rgb

class HSVSlider(QSlider):
    """
    Horizontal slider that paints a gradient in the groove and a circular indicator.
    Designed to avoid cropping by using widget padding and respecting the style's groove rect.
    """

    def __init__(self, gradient_type, color_state, initial_value, callback):
        super().__init__(Qt.Orientation.Horizontal)
        self.gradient_type = gradient_type
        self.color_state = color_state
        self.callback = callback

        self.is_hovered = False

        self.setRange(0, 100)
        self.setValue(initial_value)
        self.valueChanged.connect(self.on_value_changed)

        # Ensure there's enough height to paint the groove + indicator without clipping.
        self.setMinimumHeight(42)
        self.setMinimumWidth(22 * 8)

        # Remove any fixed width: let layout decide. Fixed widths were causing cropping previously.

        # Minimal stylesheet: hide the default handle visuals so we can draw a custom indicator.


    def on_value_changed(self, value):
        # propagate up and repaint (so indicator moves and dependent gradients update)
        try:
            self.callback(value)
        except Exception:
            # don't let exceptions stop UI refresh; still update
            pass
        self.update()

    def enterEvent(self, event):
        play_sound("hover")
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        # Custom painting of the gradient groove and circular handle
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Use the style's groove rect so we match platform metrics.
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)

        # Build the gradient according to type
        gradient = QLinearGradient(groove_rect.left(), groove_rect.top(), groove_rect.right(), groove_rect.top())
        num_steps = 24

        if self.gradient_type == 'hue':
            for i in range(num_steps + 1):
                t = i / num_steps
                hue = t  # 0..1
                color = QColor.fromHsvF(hue, 1.0, 1.0)
                gradient.setColorAt(t, color)
        elif self.gradient_type == 'saturation':
            h = float(self.color_state.get('h', 0.0))
            v = float(self.color_state.get('v', 1.0))
            for i in range(num_steps + 1):
                t = i / num_steps
                sat = t
                r, g, b, _ = hsv_to_rgb(h, sat, v)
                gradient.setColorAt(t, QColor.fromRgbF(float(r), float(g), float(b)))
        elif self.gradient_type == 'value':
            h = float(self.color_state.get('h', 0.0))
            s = float(self.color_state.get('s', 1.0))
            for i in range(num_steps + 1):
                t = i / num_steps
                val = t
                r, g, b, _ = hsv_to_rgb(h, s, val)
                gradient.setColorAt(t, QColor.fromRgbF(float(r), float(g), float(b)))
        elif self.gradient_type == 'alpha':
            h = float(self.color_state.get('h', 0.0))
            s = float(self.color_state.get('s', 0.0))
            v = float(self.color_state.get('v', 1.0))
            r, g, b, _ = hsv_to_rgb(h, s, v)
            for i in range(num_steps + 1):
                t = i / num_steps
                a = t ** 2  # Non-linear transition: quadratic easing for better low-alpha visibility
                # QColor.fromRgbF accepts alpha as 4th arg
                gradient.setColorAt(t, QColor.fromRgbF(float(r), float(g), float(b), float(a)))
        else:
            # fallback: neutral grey gradient
            gradient.setColorAt(0.0, QColor(40, 40, 40))
            gradient.setColorAt(1.0, QColor(200, 200, 200))

        # Draw rounded gradient bar
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        radius = min(22.0, groove_rect.height() / 2.0)
        painter.drawRoundedRect(groove_rect, radius, radius)
        painter.restore()

        # Draw circular indicator (centered on groove, guaranteed to be inside widget)
        pos_fraction = (self.value() - self.minimum()) / max(1, (self.maximum() - self.minimum()))
        cx = groove_rect.left() + pos_fraction * groove_rect.width()
        cy = groove_rect.center().y()
        handle_radius = groove_rect.height() * 0.4

        # Dynamic pen width based on hover
        pen_width = 3.5 if self.is_hovered else 2.0
        half_pen = pen_width / 2.0

        # Clamp cx to keep the handle fully within widget bounds, with extra 2px margin
        widget_width = self.width()
        cx = max(handle_radius + half_pen + 2, min(cx, widget_width - handle_radius - half_pen - 2))

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # White outer ring
        painter.setPen(QPen(QColor("white"), pen_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(cx - handle_radius, cy - handle_radius, handle_radius * 2.0, handle_radius * 2.0))
        painter.restore()


def obj_color(self, position, callback=None):
    config = ContextMenuConfig()
    config.anchor = "+y"
    config.close_on_outside = False
    config.auto_close = True
#
    options_list = ["H", "S", "V", "A", ic.ICON_IMAGE, ic.ICON_CLOSE_RADIAL,]

    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return
    obj = selected[0]

    # get current color in rgba float [0..1]

    h, s, v, _ = rgb_to_hsv(obj.get_color())
    a = obj.get_alpha()


    # convert to 0..100 slider space
    color_state = {
        "h": float(h),  # 0..1
        "s": float(s),
        "v": float(v),
        "a": float(a),
    }

    h_pct = int(color_state["h"] * 100)
    s_pct = int(color_state["s"] * 100)
    v_pct = int(color_state["v"] * 100)
    a_pct = int(color_state["a"] * 100)

    def make_callback(component):
        def callback(value):
            val = float(value) / 100.0
            color_state[component.lower()] = val

            # Update dependent sliders' gradients
            if component == "H":
                sat_slider.update()
                val_slider.update()
                alpha_slider.update()
            elif component == "S":
                val_slider.update()
                alpha_slider.update()
            elif component == "V":
                sat_slider.update()
                alpha_slider.update()

            r, g, b, _ = hsv_to_rgb(color_state["h"], color_state["s"], color_state["v"])
            alpha = color_state["a"]

            new_color = (float(r), float(g), float(b))
            if VispyColor is not None:
                new_color = VispyColor(new_color)
            obj.set_color(new_color)
            obj.set_alpha(float(alpha))

        return callback

    hue_slider = HSVSlider('hue', color_state, h_pct, make_callback("H"))
    sat_slider = HSVSlider('saturation', color_state, s_pct, make_callback("S"))
    val_slider = HSVSlider('value', color_state, v_pct, make_callback("V"))
    alpha_slider = HSVSlider('alpha', color_state, a_pct, make_callback("A"))

    config.custom_widget_items = {
        "H": hue_slider,
        "S": sat_slider,
        "V": val_slider,
        "A": alpha_slider,
    }

    config.image_items = {
        ic.ICON_IMAGE: obj.texture_path if hasattr(obj, 'texture_path') else None,
        }
    
    config.use_extended_shape_items = {ic.ICON_IMAGE: (True,True) if obj.texture_path else True, 
                                       ic.ICON_CLOSE_RADIAL: False,}

    def load_image(image_path):
        if image_path == None:
            image_path, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if image_path:
            obj.set_texture(image_path)
            ctx.update_item(ic.ICON_IMAGE, "image_path", image_path)



    config.callbackL = {
        ic.ICON_IMAGE: lambda: load_image(None),
        ic.ICON_CLOSE_RADIAL: lambda: (ctx.close(), callback(self))
    }

    config.callbackR = { ic.ICON_CLOSE_RADIAL: lambda value: ctx.move(  self.central_widget.mapFromGlobal(QCursor.pos())- QPoint(ctx.width()//2, ctx.height() - config.item_radius) )
    }
    config.slider_values = {ic.ICON_CLOSE_RADIAL: (0,1,0)}
    config.slider_color = {ic.ICON_CLOSE_RADIAL: QColor(150, 150, 150, 0)}



    config.extra_distance = [0,(config.item_radius * 2) - 6 ]

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )

    