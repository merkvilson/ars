from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QGraphicsBlurEffect

def open_effect(widget, duration: int = 200, start_radius: int = 50):
    """
    Show the window with an animated blur that decreases from start_radius to 0.
    """
    # Apply blur effect if not already attached
    if not hasattr(widget, "_blur_effect") or widget.graphicsEffect() != widget._blur_effect:
        widget._blur_effect = QGraphicsBlurEffect(widget)
        widget.setGraphicsEffect(widget._blur_effect)

    widget._blur_effect.setBlurRadius(start_radius)

    # Show the window before animation
    widget.show()
    widget.raise_()
    widget.activateWindow()
    widget.setFocus()   

    # Animate blur radius from start_radius → 0
    anim = QPropertyAnimation(widget._blur_effect, b"blurRadius", widget)
    anim.setDuration(duration)
    anim.setStartValue(start_radius)
    anim.setEndValue(0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # Remove the effect when animation finishes to restore performance
    def on_finished():
        widget.setGraphicsEffect(None)

    anim.finished.connect(on_finished)

    # Keep reference so it’s not garbage-collected
    widget._blur_anim = anim
    anim.start()

def close_effect(widget, duration: int = 250, end_radius: int = 50):
    """
    Close the window with an animated blur that increases from 0 to end_radius.
    """
    # Ensure effect is attached (it might have been removed by open_effect)
    if not hasattr(widget, "_blur_effect") or widget.graphicsEffect() != widget._blur_effect:
        widget._blur_effect = QGraphicsBlurEffect(widget)
        widget.setGraphicsEffect(widget._blur_effect)

    # Ensure blur starts from current radius (likely 0)
    widget._blur_effect.setBlurRadius(0)

    anim = QPropertyAnimation(widget._blur_effect, b"blurRadius", widget)
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(end_radius)
    anim.setEasingCurve(QEasingCurve.Type.InCubic)

    # When animation finishes, close the window
    anim.finished.connect(widget.close)
    try:
        widget.window().viewport._canvas.native.setFocus()
    except AttributeError:
        pass

    widget._blur_anim = anim  # keep reference
    anim.start()
