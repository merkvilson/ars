import re
from pathlib import Path
import os

font_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(font_dir, "style.css")

# Regex to match `.icon-name:before { content: "\e900"; }`
pattern = re.compile(
    r"\.icon-([a-zA-Z0-9\-_]+):before\s*{\s*content:\s*\"\\(e[0-9a-fA-F]+)\";",
    re.MULTILINE,
)

def _load_icons():
    css_text = Path(file_path).read_text(encoding="utf-8")
    matches = pattern.findall(css_text)
    globals_dict = globals()
    icon_values = []

    for name, hex_value in matches:
        var_name = "ICON_" + name.upper().replace("-", "_")
        codepoint = int(hex_value, 16)   # convert "e900" -> int
        char_value = chr(codepoint)      # turn into real Unicode char
        globals_dict[var_name] = char_value
        icon_values.append(char_value)

    # Store all actual characters in one list
    globals_dict["ICON_FULL_LIST"] = icon_values

# Initialize on import
_load_icons()