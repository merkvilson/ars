import webcolors
from colorsys import hsv_to_rgb

def get_color_name(color):
    """
    Convert a color (RGB, HSV, or HEX) into a human-readable name.
    Works with all versions of `webcolors`.
    """

    # --- Normalize to RGB (0–255) ---
    if isinstance(color, str):
        if not color.startswith('#'):
            color = '#' + color
        rgb = webcolors.hex_to_rgb(color)
        rgb = (rgb.red, rgb.green, rgb.blue)

    elif isinstance(color, (tuple, list)) and len(color) == 3:
        if all(0 <= c <= 1 for c in color):
            # Assume HSV (values 0–1)
            rgb_norm = hsv_to_rgb(*color)
            rgb = tuple(int(c * 255) for c in rgb_norm)
        else:
            # Assume RGB (0–255)
            rgb = tuple(int(c) for c in color)
    else:
        raise ValueError("Unsupported color format.")

    # --- Try exact match ---
    try:
        return webcolors.rgb_to_name(rgb)
    except ValueError:
        pass

    # --- Fallback: closest color ---
    # Build a CSS3 color dictionary that works for all versions
    try:
        color_dict = webcolors.CSS3_NAMES_TO_HEX  # old versions
    except AttributeError:
        # manually rebuild dictionary
        color_dict = {n: webcolors.name_to_hex(n) for n in webcolors._definitions._CSS3_NAMES_TO_HEX.keys()} \
                     if hasattr(webcolors, "_definitions") else \
                     {n: webcolors.name_to_hex(n) for n in webcolors.HTML4_NAMES_TO_HEX.keys()}

    # Find nearest color
    min_dist = float("inf")
    closest_name = None

    for name, hex_value in color_dict.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(hex_value)
        dist = (r_c - rgb[0]) ** 2 + (g_c - rgb[1]) ** 2 + (b_c - rgb[2]) ** 2
        if dist < min_dist:
            min_dist = dist
            closest_name = name

    return closest_name


# --- Examples ---
print(get_color_name((255, 151, 0)))       # → red
print(get_color_name((0, 255, 0)))       # → lime
print(get_color_name("#0000ff"))         # → blue
print(get_color_name((0.5, 1, 1)))       # → cyan
print(get_color_name((255, 20, 0)))      # → red or orangered (closest)
