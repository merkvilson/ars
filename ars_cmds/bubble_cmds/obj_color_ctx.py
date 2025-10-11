from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *
import numpy as np
import theme.fonts.new_fonts as RRRFONT
from vispy.color import Color as VispyColor



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


def BBL_OBJ_BOX(self, position):
    config = ContextMenuConfig()
    config.item_radius = 14
    config.font = RRRFONT.get_font(14)
    config.item_spacing = 28
    config.auto_close = False
    config.show_value = True

    options_list = ["H", "S", "V", "A", "W","X", "Y", "Z"]

    config.image_items = { "H": r"C:\Users\gmerk\OneDrive\Pictures\h0lBtpi.jpeg"}
    config.use_extended_shape_items = {"H": (True,False),}

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

    h_pct = color_state["h"] * 100.0
    s_pct = color_state["s"] * 100.0
    v_pct = color_state["v"] * 100.0
    a_pct = color_state["a"] * 100.0

    # callback factory: updates color_state and sets the object's color
    def make_callback(component):
        def callback(value):
            # value is slider value in the UI: 0..100
            try:
                val = float(value)
            except Exception:
                # if UI sends (min,max,current) tuple or other shape, try to extract numeric
                val = float(value[2]) if isinstance(value, (tuple, list)) and len(value) > 2 else 0.0

            color_state[component] = val / 100.0

            # convert HSV (0..1) -> RGB
            r, g, b, _ = hsv_to_rgb(color_state["h"], color_state["s"], color_state["v"])
            alpha = color_state["a"]

            # try to set the color on the object (vispy Color preferred)
            try:
                new_color = (float(r), float(g), float(b))
                if VispyColor is not None:
                    new_color = VispyColor(new_color)
                obj.set_color(new_color)
                obj.set_alpha(float(alpha))
            except Exception as e:
                print("Failed to set object color or alpha:", e)

        return callback

    # attach callbacks for H, S, V, A
    config.callbackL = {
        "H": make_callback("h"),
        "S": make_callback("s"),
        "V": make_callback("v"),
        "A": make_callback("a"),
        "W": lambda: obj.set_wireframe(not obj.get_wireframe()),
        "X": lambda: obj.set_shading(None),
        "Y": lambda: obj.set_shading('flat'),
        "Z": lambda: obj.set_shading('smooth'),

    }

    # slider_values expects (min, max, current)
    config.slider_values = {
        "H": (0, 100, h_pct),
        "S": (0, 100, s_pct),
        "V": (0, 100, v_pct),
        "A": (0, 100, a_pct),
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )