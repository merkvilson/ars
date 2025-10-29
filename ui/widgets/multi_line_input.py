from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QTextCursor


class MultiLineInputWidget(QWidget):
    """A multi-line text input widget with a custom-painted background."""
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # --- Layout and Widgets ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Text area
        self.text_edit = QTextEdit(self)

        
        self.text_edit.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.text_edit)

        # Hint Label
        self.hint_label = QLabel("Prompt Editor", self)
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setVisible(True)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.hint_label)

        # --- Styling ---
        self.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(0, 0, 0, 60);
                border: none;
                color: rgba(255, 255, 255, 220);
                selection-background-color: rgba(255, 255, 255, 60);
            }}
            QLabel#hintLabel {{
                color: rgba(255,255,255,220);
                font-size: 12px;
                padding-right: 6px;
                padding-bottom: 2px;
            }}
        """)

        QTimer.singleShot(50, self.set_initial_focus)

    def set_initial_focus(self):
        """Set focus and move cursor to the end of the text."""
        self.text_edit.setFocus()
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_edit.setTextCursor(cursor)

    def paintEvent(self, e):
        """Paints the rounded rectangle background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        
        painter.fillPath(path, QColor(100, 100, 100, 100))
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
        painter.drawPath(path)