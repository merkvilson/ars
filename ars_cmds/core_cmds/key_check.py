from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def key_check(key):
    key = key.lower()

    # Check keyboard modifiers
    modifiers = QApplication.keyboardModifiers()
    if   key == "shift": result = modifiers & Qt.KeyboardModifier.ShiftModifier
    elif key == "ctrl":  result = modifiers & Qt.KeyboardModifier.ControlModifier
    elif key == "alt":   result = modifiers & Qt.KeyboardModifier.AltModifier
    elif key == "meta":  result = modifiers & Qt.KeyboardModifier.MetaModifier
    
    # Check mouse buttons
    elif key == "l":   result = QApplication.mouseButtons() & Qt.MouseButton.LeftButton
    elif key == "r":  result = QApplication.mouseButtons() & Qt.MouseButton.RightButton
    elif key == "m": result = QApplication.mouseButtons() & Qt.MouseButton.MiddleButton
    
    else: result = None

    return result
