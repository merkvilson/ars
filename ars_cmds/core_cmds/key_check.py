from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer


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



def key_check_continuous(callback=None, key='l', interval=100, callback_start=None, callback_end=None):
    """
    Continuously check if a key/button is held down and execute callbacks.
    
    Args:
        callback: Function to call repeatedly while key is held
        key: Key to monitor ('l', 'r', 'm', 'shift', 'ctrl', 'alt', 'meta')
        interval: Check interval in milliseconds
        callback_start: Function to call once when monitoring starts
        callback_end: Function to call once when key is released
    
    Returns:
        QTimer object that can be stopped manually if needed
    """
    if callback_start:
        callback_start()
    
    # Create a new timer to check key state
    check_timer = QTimer()
    
    def check_key_state():
        if key_check(key):
            if callback:
                callback()
        else:
            # Key released - cleanup
            check_timer.stop()
            if callback_end:
                callback_end()
            check_timer.deleteLater()
    
    check_timer.timeout.connect(check_key_state)
    check_timer.start(interval)
    
    # Execute once immediately
    check_key_state()
    
    return check_timer