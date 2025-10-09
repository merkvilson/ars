import os
from typing import Optional, Callable
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import QEvent, QPoint, QObject, Qt, QTimer
from .hotkey_profile import HotkeyProfile

from ui.widgets.context_menu import ContextButtonWindow

def hotkey_radials(main_window):
    hotkey_items = False
    radial_menus = main_window.central_widget.findChildren(ContextButtonWindow)
    for menu in radial_menus:
        if menu.isVisible() and bool(menu.config.hotkey_items): 
            hotkey_items = True
            break
    return hotkey_items


class HotkeyManager(QObject):  # Inherit from QObject
    """Manages hotkey profiles, action registration, and dynamic binding."""
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)  # Initialize QObject with parent
        self.parent = parent
        self.actions: dict[str, Callable] = {}  # action_name: function
        self.profiles: dict[str, HotkeyProfile] = {}  # name: profile
        self.current_profile: Optional[HotkeyProfile] = None
        self.shortcuts: list[QShortcut] = []  # Active shortcuts to manage
        self.user_dir = os.path.join("hotkeys", "user")
        os.makedirs(self.user_dir, exist_ok=True)
        self.wheel_bindings = {}  # key_str (e.g., "Shift+mouse-wheel-up"): action_name
        self.radials_present = False  # Track radial hotkey conflict
        self.parent.installEventFilter(self)
        
        # Poll for dynamic radial changes
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_radials)
        self.check_timer.start(50)  # Check every 500ms

    def _check_radials(self) -> None:
        """Periodically check for radial hotkeys and toggle bindings."""
        main_window = self.parent.window()
        if not main_window:
            return
        new_state = hotkey_radials(main_window)
        if self.radials_present != new_state:
            self.radials_present = new_state
            if self.radials_present:
                print("Hotkeys disabled: radial menu has hotkey_items.")
                self._unbind_all()
            elif self.current_profile:
                self._bind_shortcuts()  # Re-bind if profile loaded

    def eventFilter(self, obj, event) -> bool:
        """Capture and handle mouse wheel events if bound and no radial conflict."""
        if event.type() == QEvent.Type.Wheel:
            main_window = self.parent.window()
            if main_window:
                new_state = hotkey_radials(main_window)
                if self.radials_present != new_state:
                    self.radials_present = new_state
                    if self.radials_present:
                        print("Hotkeys disabled: radial menu has hotkey_items.")
                        self._unbind_all()
                    elif self.current_profile:
                        self._bind_shortcuts()  # Re-bind if profile loaded
                if self.radials_present:
                    return True  # Consume without execution
            
            if not self.radials_present:
                delta = event.angleDelta().y()  # Positive = up, negative = down
                direction = "up" if delta > 0 else "down"
                
                modifiers = event.modifiers()
                mods = []
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    mods.append("Shift")
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    mods.append("Ctrl")
                if modifiers & Qt.KeyboardModifier.AltModifier:
                    mods.append("Alt")
                if modifiers & Qt.KeyboardModifier.MetaModifier:
                    mods.append("Meta")
                
                mod_str = "+".join(sorted(mods)) + "+" if mods else ""
                key_str = mod_str + "mouse-wheel-" + direction
                
                if key_str in self.wheel_bindings:
                    action_name = self.wheel_bindings[key_str]
                    self.actions[action_name]()  # Execute the bound function
                    return True  # Consume the event (prevent propagation)
        
        return super().eventFilter(obj, event)  # Fallback for other events

    def register_action(self, action_name: str, func: Callable) -> None:
        """Register an action that can be bound to a hotkey."""
        self.actions[action_name] = func

    def add_profile(self, profile: HotkeyProfile) -> None:
        """Add a profile to memory."""
        self.profiles[profile.name] = profile

    def load_profile(self, name: str) -> None:
        """Load and activate a profile (from memory or file)."""
        if name in self.profiles:
            profile = self.profiles[name]
        else:
            path = os.path.join(self.user_dir, f"{name}.json")
            profile = HotkeyProfile.load_from_json(path)
            self.add_profile(profile)
        
        self._unbind_all()
        self.current_profile = profile
        self._bind_shortcuts()

    def save_current_profile(self, name: Optional[str] = None) -> None:
        """Save the current profile to JSON (optionally rename)."""
        if not self.current_profile:
            raise ValueError("No current profile to save.")
        if name:
            self.current_profile.name = name
        path = os.path.join(self.user_dir, f"{self.current_profile.name}.json")
        self.current_profile.save_to_json(path)
        self.add_profile(self.current_profile)  # Update in-memory

    def update_binding(self, action_name: str, key_str: str) -> None:
        """Update a binding in the current profile and rebind (for editing)."""
        if self.current_profile and action_name in self.actions:
            self.current_profile.bindings[action_name] = key_str
            self._unbind_all()
            self._bind_shortcuts()

    def _bind_shortcuts(self) -> None:
        """Bind QShortcuts based on current profile if no radial conflict."""
        if not self.current_profile:
            return
        main_window = self.parent.window()
        new_state = hotkey_radials(main_window) if main_window else False
        if self.radials_present != new_state:
            self.radials_present = new_state
            if self.radials_present:
                print("Hotkeys disabled: radial menu has hotkey_items.")
                self._unbind_all()
                return
        if self.radials_present:
            self.wheel_bindings.clear()  # Clear even if no shortcuts
            return
        self.wheel_bindings.clear()  # Reset wheel bindings
        for action_name, key_str in self.current_profile.bindings.items():
            if action_name in self.actions:
                if "mouse-wheel-" in key_str:
                    self.wheel_bindings[key_str] = action_name
                else:
                    seq = QKeySequence.fromString(key_str)
                    shortcut = QShortcut(seq, self.parent)
                    shortcut.activated.connect(self.actions[action_name])
                    self.shortcuts.append(shortcut)

    def _unbind_all(self) -> None:
        """Unbind and clear all active shortcuts."""
        for shortcut in self.shortcuts:
            shortcut.setEnabled(False)
            shortcut.setParent(None)  # Allows deletion
        self.shortcuts = []
        self.wheel_bindings.clear()