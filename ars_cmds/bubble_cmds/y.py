from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from PyQt6.QtCore import Qt
from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts.font_icons import *  # Uncomment if you need font icons

class GradientWidget(QWidget):
    """Simple gradient widget that fills its area with a color gradient."""
    
    def __init__(self, color1=QColor(100, 150, 255), color2=QColor(255, 100, 150), parent=None):
        super().__init__(parent)
        self.color1 = color1
        self.color2 = color2
        # Fixed: In PyQt6, use Qt.WidgetAttribute directly (no need for .WidgetAttribute)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        # Fixed: In PyQt6, use QPainter.RenderHint directly (no need for .RenderHint)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create horizontal gradient (left to right)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, self.color1)
        gradient.setColorAt(1, self.color2)
        
        painter.fillRect(self.rect(), gradient)

def BBL_X(self, position):

    # Create the gradient widget
    custom_widget = GradientWidget(
        color1=QColor(70, 120, 200, 255),  # Blue-ish (with transparency)
        color2=QColor(150, 70, 200, 255)   # Purple-ish (with transparency)
    )


    config = ContextMenuConfig()
    config.auto_close = False
    config.color = {"X": QColor(255,0,0,0)}
    
    # These are the 3 buttons that will appear
    options_list = ["X", "Y", "Z"]

    # Z button gets a slider (min: 0, max: 100, current: 30)
    config.slider_values = {"Z": (0, 100, 30)}

    config.inner_widgets = {"X": custom_widget}
    
    # Labels for each button
    config.additional_texts = {
        "X": "Clone object",
        "Y": "Print bbox",
        "Z": "Add mesh"
    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )
    
    return ctx  # Return the context menu if you need to handle its result