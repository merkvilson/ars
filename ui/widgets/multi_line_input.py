# multi_line_input.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen

class MultiLineInputConfig:
    """Configuration class for MultiLineInputWidget."""
    def __init__(self):
        # Dimensions
        self.border_radius = 10
        # Behavior
        self.show_shortcut_hint = True
        # Style
        self.bg_color = QColor(100, 100, 100, 100)
        self.border_color = QColor(255, 255, 255, 40)
        self.text_color = QColor(255, 255, 255, 220)
        self.font_family = "Segoe UI"
        self.font_size = 12
        self.hint_text = "Prompt Editor"


class MultiLineInputWidget(QWidget):
    """A multi-line text input widget with a custom-painted background."""
    def __init__(self,  default_object = None):
        super().__init__()
        self.config = MultiLineInputConfig()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.default_object = default_object

        # --- Layout and Widgets ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Text area
        self.text_edit = QTextEdit(self)

        if self.default_object:
            self.text_edit.setPlainText(default_object.prompt)
        
        self.text_edit.setFont(QFont(self.config.font_family, self.config.font_size))
        layout.addWidget(self.text_edit)

        # Hint Label
        self.hint_label = QLabel(self.config.hint_text, self)
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setVisible(self.config.show_shortcut_hint)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.hint_label)

        # --- Styling ---
        self.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(0, 0, 0, 60);
                border: none;
                color: rgb({self.config.text_color.red()}, {self.config.text_color.green()}, {self.config.text_color.blue()});
                selection-background-color: rgba(255, 255, 255, 60);
            }}
            QLabel#hintLabel {{
                color: rgba(255,255,255,220);
                font-size: 12px;
                padding-right: 6px;
                padding-bottom: 2px;
            }}
        """)

        self.text_edit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        if self.default_object:
            self.default_object.prompt = self.text_edit.toPlainText()

    def paintEvent(self, e):
        """Paints the rounded rectangle background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, self.config.border_radius, self.config.border_radius)
        
        painter.fillPath(path, self.config.bg_color)
        painter.setPen(QPen(self.config.border_color, 1))
        painter.drawPath(path)