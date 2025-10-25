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

def _unwrap_color_obj(color):
    """
    Try many ways to extract an (r,g,b,a) sequence of floats from `color`.
    Returns a tuple (r, g, b, a) as Python floats.
    """
    # Case: user passed r,g,b(,a) as separate args that arrived as a tuple/list
    if isinstance(color, (tuple, list)) and len(color) in (3, 4) and all(
        not hasattr(x, "__iter__") for x in color
    ):
        arr = np.array(color, dtype=float)

    # Case: nested single-item tuple/list like ((r,g,b,a),)
    elif isinstance(color, (tuple, list)) and len(color) == 1 and isinstance(color[0], (tuple, list, np.ndarray)):
        arr = np.array(color[0], dtype=float)

    else:
        # Try common attributes/properties (vispy, matplotlib-like, etc.)
        try:
            rgba = getattr(color, "rgba", None)
            if callable(rgba):
                rgba = rgba()
            if rgba is not None:
                arr = np.asarray(rgba, dtype=float)
            else:
                colors = getattr(color, "colors", None)
                if colors is not None:
                    arr = np.asarray(colors, dtype=float)
                    if arr.ndim > 1:
                        arr = arr[0]  # take first color
                else:
                    for attr in ("get_color", "get_rgba", "to_rgba", "rgba"):
                        fn = getattr(color, attr, None)
                        if fn is not None:
                            val = fn() if callable(fn) else fn
                            arr = np.asarray(val, dtype=float)
                            break
                    else:
                        arr = np.asarray(color, dtype=float)
        except Exception:
            raise TypeError(f"Unsupported color type: {type(color)}")

    arr = np.asarray(arr).flatten()

    if arr.size == 3:
        r, g, b = arr
        a = 1.0
    elif arr.size >= 4:
        r, g, b, a = arr[:4]
    else:
        raise ValueError(f"Could not extract RGB(A) from color object: {repr(color)}")

    return float(r), float(g), float(b), float(a)

def rgb_to_hsv(*args):
    """
    Convert RGB(A) -> HSV(A).
    Accepts:
      - rgb_to_hsv(r, g, b)
      - rgb_to_hsv(r, g, b, a)
      - rgb_to_hsv(color) where color may be tuple/list/np.array/vispy Color/ColorArray
    Returns: (h, s, v, a) as np.float32 in [0..1]
    """
    if len(args) == 0:
        raise TypeError("rgb_to_hsv requires at least one argument")

    if len(args) > 1:
        color = args
    else:
        color = args[0]

    r, g, b, a = _unwrap_color_obj(color)

    mx = max(r, g, b)
    mn = min(r, g, b)
    diff = mx - mn

    eps = 1e-12
    if diff <= eps:
        h = 0.0
    elif mx == r:
        h = ((g - b) / diff) % 6
    elif mx == g:
        h = ((b - r) / diff) + 2
    else:
        h = ((r - g) / diff) + 4
    h = h / 6.0

    s = 0.0 if mx <= eps else (diff / mx)
    v = mx

    return np.float32(h), np.float32(s), np.float32(v), np.float32(a)

def hsv_to_rgb(h, s, v, a=1.0):
    """
    Convert HSV -> RGB. Inputs h,s,v in [0..1]. Returns r,g,b,a as np.float32 in [0..1].
    """
    # accept sequences too
    if isinstance(h, (tuple, list, np.ndarray)):
        seq = list(h)
        if len(seq) >= 3:
            h, s, v = seq[0], seq[1], seq[2]
        if len(seq) >= 4:
            a = seq[3]

    h = float(h) % 1.0
    s = float(s)
    v = float(v)
    a = float(a)

    if s == 0.0:
        r = g = b = v
        return np.float32(r), np.float32(g), np.float32(b), np.float32(a)

    h6 = h * 6.0
    i = int(h6)  # 0..5
    f = h6 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))

    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q

    return np.float32(r), np.float32(g), np.float32(b), np.float32(a)

def obj_color(self, position):
    config = ContextMenuConfig()
    config.anchor = "+y"
    config.close_on_outside = False
    config.auto_close = True
#
    options_list = ["H", "S", "V", "A", ic.ICON_IMAGE, "?", ic.ICON_CLOSE_RADIAL,]

    selected = self.viewport._objectManager.get_selected_objects()
    if not selected:
        return
    obj = selected[0]

    # get current color in rgba float [0..1]
    try:
        h, s, v, _ = rgb_to_hsv(obj.get_color())
        a = obj.get_alpha()
    except Exception as e:
        # debug fallback: print type and repr so you can iterate if other cases appear
        c = obj.get_color()
        print("rgb_to_hsv failed, color repr:", type(c), repr(c))
        raise

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
        "?":  obj.alpha_map_path if hasattr(obj, 'alpha_map_path') else None,}
    
    config.use_extended_shape_items = {ic.ICON_IMAGE: (True,False) if hasattr(obj, 'texture_path') else False, 
                                       "?": (True,False) if hasattr(obj, 'alpha_map_path') else False,
                                       ic.ICON_CLOSE_RADIAL: False,}

    def load_image(image_path):
        if image_path == None:
            image_path, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if image_path:
            obj.set_texture(image_path)
            ctx.update_item(ic.ICON_IMAGE, "image_path", image_path)


    def load_alpha_img(image_path):
        if image_path == None:
            image_path, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if image_path:
            obj.set_alpha_map(image_path)
            ctx.update_item("?", "image_path", image_path)    

    config.callbackL = {
        ic.ICON_IMAGE: lambda: load_image(None),
        "?": lambda: load_alpha_img(None),
        ic.ICON_CLOSE_RADIAL: lambda: print(obj.texture_path),
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

    