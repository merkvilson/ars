import json
from PyQt6.QtGui import QColor

with open(r'theme\colors\colors.json', 'r') as f:
    rgba = json.load(f)


button_color = QColor(70, 70, 70, 200) or "#21252b"
hover_color = QColor(150, 150, 150, 200) or "#3e4451"
symbol_color = QColor(255, 255, 255, 180) or "#abb2bf"
additional_text_color = QColor(255, 255, 255, 180) or "#abb2bf"
hotkey_text_color = QColor(255, 255, 255, 180) or "#abb2bf"
slider_color = QColor(150, 150, 150, 150) or "#969696"
toggle_color = QColor(100, 120, 170, 200) or "#6478aa"

toggle_hover_color =    QColor(120, 150, 255, 230) or "#7896ff"
slider_progress_color = QColor(120, 150, 255, 230) or "#7896ff"

toggle_disabled_color = QColor(0, 0, 10, 100) or "#00000a"
toggle_disabled_hover_color = QColor(60, 75, 125, 200) or "#3c4b7d"

