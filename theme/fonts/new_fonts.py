# theme/fonts/new_fonts.py
import os

# Default fallback
FONT_FAMILY = "Arial"

FONT_FAMILIES = {}

def get_font(size=10, font_name="icomoon.ttf", weight=None):
    from PyQt6.QtGui import QFont, QFontDatabase
    from PyQt6.QtWidgets import QApplication
    if QApplication.instance() is not None and font_name not in FONT_FAMILIES:
        font_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(font_dir, font_name)
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    FONT_FAMILIES[font_name] = families[0]
    family = FONT_FAMILIES.get(font_name, "Arial")
    return QFont(family, size, weight or QFont.Weight.Bold)
