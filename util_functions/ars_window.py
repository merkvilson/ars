"""Utilities for retrieving the running Airen Studio main window.

Usage
-----
>>> from util_functions.ars_window import ars_window
>>> main = ars_window()
>>> print(main)
<ui.main_window.MainWindow object at 0x...>
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Type

from importlib import import_module

from PyQt6.QtWidgets import QApplication, QWidget

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from typing import Iterable
    from ui.main_window import MainWindow

_cached_window: Optional["MainWindow"] = None
_main_window_type: Optional[Type["MainWindow"]] = None


def _get_main_window_type() -> Optional[Type["MainWindow"]]:
    """Load and cache the ``ui.main_window.MainWindow`` type lazily."""

    global _main_window_type

    if _main_window_type is None:
        try:
            module = import_module("ui.main_window")
            _main_window_type = getattr(module, "MainWindow")
        except (ImportError, AttributeError):
            return None

    return _main_window_type


def _is_valid_window(widget: Optional[QWidget]) -> bool:
    """Return True when *widget* is an existing MainWindow instance."""
    if widget is None:
        return False

    main_window_type = _get_main_window_type()
    if main_window_type is None:
        return False

    try:
        return isinstance(widget, main_window_type)
    except RuntimeError:
        # Happens when the underlying C++ object has been deleted.
        return False


def _locate_from_widgets(widgets: "Iterable[QWidget]") -> Optional[MainWindow]:
    for widget in widgets:
        if _is_valid_window(widget):
            return widget  # type: ignore[return-value]
    return None


def ars_window(strict: bool = True) -> Optional[MainWindow]:
    """Return the active :class:`ui.main_window.MainWindow` instance.

    The function performs a few steps:
    1. Reuses a cached reference when it is still valid.
    2. Walks the current ``QApplication`` top-level widgets.
    3. Falls back to ``QApplication.activeWindow()``.

    Args:
        strict: When ``True`` (default) a ``RuntimeError`` is raised if the
            window cannot be located. When ``False`` the function simply
            returns ``None``.

    Returns:
        The live ``MainWindow`` instance, allowing call sites across the code
        base to avoid threading ``self`` around.
    """

    global _cached_window

    if _is_valid_window(_cached_window):
        return _cached_window

    app = QApplication.instance()
    if app is None:
        if strict:
            raise RuntimeError("No running QApplication instance; ars_window is unavailable.")
        return None

    # Try every top-level widget first
    match = _locate_from_widgets(app.topLevelWidgets())
    if match is None:
        # Fall back to the currently active window
        match = app.activeWindow()

    if not _is_valid_window(match):
        if strict:
            raise RuntimeError("No MainWindow instance is currently registered.")
        return None

    _cached_window = match  # type: ignore[assignment]
    return match


__all__ = ["ars_window"]



#Alternative simpler implementation
# from PyQt6.QtWidgets import QApplication
# QApplication.instance().activeWindow() # This returns the main window instance