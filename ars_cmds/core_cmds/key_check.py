from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer, QObject, QEvent
import ctypes


def key_check(key):
    key = key.lower()

    # Check keyboard modifiers
    modifiers = QApplication.keyboardModifiers()
    if   key == "shift": result = modifiers & Qt.KeyboardModifier.ShiftModifier
    elif key == "ctrl":  result = modifiers & Qt.KeyboardModifier.ControlModifier
    elif key == "alt":   result = modifiers & Qt.KeyboardModifier.AltModifier
    elif key == "meta":  result = modifiers & Qt.KeyboardModifier.MetaModifier
    
    # Check mouse buttons
    elif key == "left":   result = QApplication.mouseButtons() & Qt.MouseButton.LeftButton
    elif key == "right":  result = QApplication.mouseButtons() & Qt.MouseButton.RightButton
    elif key == "middle": result = QApplication.mouseButtons() & Qt.MouseButton.MiddleButton
    
    # Check alphabet keys (Windows)
    elif len(key) == 1 and key.isalpha():
        result = ctypes.windll.user32.GetAsyncKeyState(ord(key.upper())) & 0x8000

    else: result = None

    return result

#TODO move scroll filter to its own file to use with hotkey_manager and prompt_editor 


class ScrollFilter(QObject):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta == 0:
                delta = event.angleDelta().x()
            if delta == 0:
                delta = event.pixelDelta().y()
            if delta == 0:
                delta = event.pixelDelta().x()
            
            if delta > 0:
                self.callback(1)
                return True
            elif delta < 0:
                self.callback(-1)
                return True
        
        return super().eventFilter(obj, event)


def key_check_continuous(callback=None, key='l', interval=100, callback_start=None, callback_end=None, scroll_callback=None):
    """
    Continuously check if a key/button is held down and execute callbacks.
    
    Args:
        callback: Function to call repeatedly while key is held
        key: Key to monitor ('left', 'right', 'middle', 'shift', 'ctrl', 'alt', 'meta', 'a'-'z')
        interval: Check interval in milliseconds
        callback_start: Function to call once when monitoring starts
        callback_end: Function to call once when key is released
        scroll_callback: Function to call when mouse wheel is scrolled (1 for up, -1 for down)
    
    Returns:
        QTimer object that can be stopped manually if needed
    """
    if callback_start:
        callback_start()
    
    scroll_filter = None
    if scroll_callback:
        scroll_filter = ScrollFilter(scroll_callback)
        QApplication.instance().installEventFilter(scroll_filter)
    
    # Create a new timer to check key state
    check_timer = QTimer(QApplication.instance())
    
    def check_key_state():
        if key_check(key):
            if callback:
                callback()
        else:
            # Key released - cleanup
            check_timer.stop()
            if callback_end:
                callback_end()
            
            if scroll_filter:
                QApplication.instance().removeEventFilter(scroll_filter)
                
            check_timer.deleteLater()
    
    check_timer.timeout.connect(check_key_state)
    check_timer.start(int(interval))
    
    # Execute once immediately
    check_key_state()
    
    return check_timer