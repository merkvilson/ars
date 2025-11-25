from PyQt6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QCursor, QColor, QFont
from .b_button import BButton, BButtonConfig
import theme.fonts.new_fonts as RRRFONT
from theme.fonts import font_icons as ic

class CursorFollowerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Layout with only QGraphicsView
        from PyQt6.QtWidgets import QVBoxLayout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Graphics view for BButton
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setStyleSheet("background: transparent; border: none;")
        self.graphics_view.setFixedSize(250, 100)  # Size for radius=16 extended shape
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-100, -40, 200, 80)  # Match view size
        self.graphics_view.setScene(self.scene)
        self.layout.addWidget(self.graphics_view)
        
        # Static BButton with extended shape
        button_config = BButtonConfig(
            symbol="?",  # Matches ICON_INFO
            radius=20,
            clip_to_shape = False,
            font=RRRFONT.get_font(20),
            additional_font=QFont("Arial", 10),
            hover_scale=1.0,  # No scaling
            additional_text="Info",
            use_extended_shape=True,  # Rounded rectangle
            editable=False  # No interactions
        )
        self.b_button = BButton(button_config)
        self.scene.addItem(self.b_button)
        # Center the BButton
        bounding = self.b_button.boundingRect()
        self.b_button.setPos(-bounding.width() / 2, -bounding.height() / 2)
        
        # Timer to follow cursor
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        
        # Hide timer for auto-hiding after inactivity
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.animated_hide)
        
        self.resize(250, 80)  # Match view size
        self.hide()  # Start hidden

    def UP(self, key = "additional_text", value = "0.0",  symbol = ic.ICON_MSG, auto_close = 1000, alpha = 60):
        """Update BButton's additional text using set_updated_config."""

        if not self.isVisible(): self.animated_show()        

        if len(value) > 13: self.b_button.set_updated_config("use_extended_shape", False)
        else: self.b_button.set_updated_config("use_extended_shape", True)
       
        self.b_button.set_updated_config(key, value)
        self.b_button.set_updated_config("symbol", symbol)        
        self.b_button.set_updated_config("color", QColor(100, 100, 100, alpha))
        
        if auto_close: self.hide_timer.start(auto_close) 

    def update_position(self):
        if self.isVisible():
            parent = self.parent()
            if parent:
                global_cursor = QCursor.pos()
                
                # Calculate constraints in global coordinates
                parent_tl = parent.mapToGlobal(QPoint(0, 0))
                min_x = parent_tl.x()
                min_y = parent_tl.y()
                max_x = min_x + parent.width() - self.width()
                max_y = min_y + parent.height() - self.height()

                x = max(min_x, min(global_cursor.x(), max_x))
                y = max(min_y, min(global_cursor.y(), max_y))
                
                self.move(x, y)
                self.raise_()

    def animated_show(self):
        """Show widget with scale and opacity animation."""
        self.b_button.setScale(0.0)
        self.b_button.setOpacity(0.0)
        self.show()
        self.timer.start(16)  # Start the follow timer
        # Animation group for scale and opacity
        from PyQt6.QtCore import QParallelAnimationGroup
        anim_group = QParallelAnimationGroup(self)
        
        scale_anim = QPropertyAnimation(self.b_button, b"scale")
        scale_anim.setDuration(200)  # Increased duration
        scale_anim.setStartValue(0.0)
        scale_anim.setEndValue(1.0)
        scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        opacity_anim = QPropertyAnimation(self.b_button, b"opacity")
        opacity_anim.setDuration(200)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        anim_group.addAnimation(scale_anim)
        anim_group.addAnimation(opacity_anim)
        anim_group.start()

    def animated_hide(self):
        """Hide widget with scale and opacity animation."""
        from PyQt6.QtCore import QParallelAnimationGroup
        anim_group = QParallelAnimationGroup(self)
        
        scale_anim = QPropertyAnimation(self.b_button, b"scale")
        scale_anim.setDuration(200)  # Increased duration
        scale_anim.setStartValue(1.0)
        scale_anim.setEndValue(0.0)
        scale_anim.setEasingCurve(QEasingCurve.Type.InBack)

        opacity_anim = QPropertyAnimation(self.b_button, b"opacity")
        opacity_anim.setDuration(200)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.InQuad)

        anim_group.addAnimation(scale_anim)
        anim_group.addAnimation(opacity_anim)
        anim_group.finished.connect(self._on_hide_finished)
        anim_group.start()

    def _on_hide_finished(self):
        self.hide()
        self.timer.stop()  # Stop the follow timer