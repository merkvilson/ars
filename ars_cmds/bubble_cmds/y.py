from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPen
from PyQt6.QtCore import Qt
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic

class GradientWidget(QWidget):
    """Simple gradient widget that fills its area with a full hue gradient."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Fixed: In PyQt6, use Qt.WidgetAttribute directly (no need for .WidgetAttribute)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.position = 0.3  # Normalized position (0.0 to 1.0), default for slider value 30/100
        
    def paintEvent(self, event):
        painter = QPainter(self)
        # Fixed: In PyQt6, use QPainter.RenderHint directly (no need for .RenderHint)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create horizontal gradient (left to right) with full hue cycle
        gradient = QLinearGradient(0, 0, self.width(), 0)
        
        # Generate colors across full hue spectrum (0 to 360 degrees, in 12 steps for smoothness)
        num_steps = 12
        for i in range(num_steps + 1):
            hue = (i / num_steps) * 360
            color = QColor.fromHsvF(hue / 360, 1.0, 1.0)  # Full saturation and value
            gradient.setColorAt(i / num_steps, color)
        
        painter.fillRect(self.rect(), gradient)
        
        # Draw unfilled white-outlined circle at position determined by self.position
        if self.width() > 0 and self.height() > 0:
            center_x = self.position * self.width()
            center_y = self.height() / 2.0
            radius = min(self.width(), self.height()) * .4
            painter.setPen(QPen(QColor("white"), 2, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                int(center_x - radius),
                int(center_y - radius),
                int(2 * radius),
                int(2 * radius)
            )

def BBL_Y(self, position):

    # Create the gradient widget
    custom_widget = GradientWidget()
    custom_widget.position = 30 / 100.0  # Set initial position based on slider default

    config = ContextMenuConfig()
    config.auto_close = False
    options_list = ["X", "Y", "Z", "A", "B", "C",]

    config.slider_values = {"X": (0, 100, 30)} #0-100 range, default 30     
    config.inner_widgets = {"X": custom_widget}
    
    # Labels for each button
    config.additional_texts = {
        "X": "Custom Widget",
        "Y": "???",
    }

#    ctx = None  # Placeholder to enable closure over ctx in lambdas
    
    config.callbackL = {
        "X": lambda: (setattr(custom_widget, 'position', ctx.get_value("X") / 100.0), custom_widget.update()),
        "Y": lambda: ctx.update_item("Y", "additional_text", str(ctx.get_value("X")))
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
    
    return ctx  # Return the context menu if you need to handle its result