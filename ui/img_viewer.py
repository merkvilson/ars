import math
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QWidget, QFileDialog
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QMouseEvent, QPen, QColor, QPainter, QBrush, QImage
from PyQt6.QtCore import Qt, QRectF, QPointF, QVariantAnimation
from PIL import Image, ImageSequence
from PyQt6.QtWidgets import QApplication
from ui.widgets.context_menu import close_all_open_context_menus

class ImageViewer(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setStyleSheet("border: none")
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.zoom_factor = 1.15
        self.min_zoom = 0.1  # Lowered to allow zoom from small initial scales
        self.max_zoom = 5.0
        self.setBackgroundBrush(QBrush(QColor(39, 41, 45, 255)))
        self.image_rect = None
        self._user_interacted = False  # Flag for auto-refit on resize

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)

        zoom = self.transform().m11()
        if zoom == 0:
            zoom = 1.0

        minor_spacing = 50
        major_spacing = 500
        minor_pen = QPen(QColor(80, 80, 80, 50), 1.5 / zoom)
        major_pen = QPen(QColor(120, 120, 120, 50), 2 / zoom)

        left = math.floor(rect.left() / minor_spacing) * minor_spacing
        top = math.floor(rect.top() / minor_spacing) * minor_spacing

        x = left
        while x < rect.right():
            if math.fabs(x % major_spacing) < 1e-6:
                painter.setPen(major_pen)
            else:
                painter.setPen(minor_pen)
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += minor_spacing

        y = top
        while y < rect.bottom():
            if math.fabs(y % major_spacing) < 1e-6:
                painter.setPen(major_pen)
            else:
                painter.setPen(minor_pen)
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += minor_spacing

        if rect.top() <= 0 <= rect.bottom():
            x_axis_pen = QPen(QColor.fromRgbF(0.9, 0.3, 0.3, 0.4), 1.8 / zoom)
            painter.setPen(x_axis_pen)
            painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))

        if rect.left() <= 0 <= rect.right():
            y_axis_pen = QPen(QColor.fromRgbF(0.3, 0.3, 0.9, 0.4), 1.8 / zoom)
            painter.setPen(y_axis_pen)
            painter.drawLine(QPointF(0, rect.top()), QPointF(0, rect.bottom()))
        

    def wheelEvent(self, event: QWheelEvent):
        factor = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
        current_zoom = self.transform().m11()
        new_zoom = current_zoom * factor
        
        update_zoom = False
        
        if self.min_zoom <= new_zoom <= self.max_zoom:
            update_zoom = True
        else:
            # new_zoom is out of bounds
            if current_zoom > self.max_zoom and factor < 1:
                # Allow zooming out if we are above max zoom
                update_zoom = True
            elif current_zoom < self.min_zoom and factor > 1:
                # Allow zooming in if we are below min zoom
                update_zoom = True
            elif self.min_zoom <= current_zoom <= self.max_zoom:
                # If we were in range, but going out, clamp to the limit
                if new_zoom > self.max_zoom:
                    factor = self.max_zoom / current_zoom
                    update_zoom = True
                elif new_zoom < self.min_zoom:
                    factor = self.min_zoom / current_zoom
                    update_zoom = True

        if update_zoom:
            self._user_interacted = True  # Mark as interacted
            cursor_pos = event.position()
            scene_pos = self.mapToScene(cursor_pos.toPoint())
            self.scale(factor, factor)
            self.centerOn(scene_pos)
            new_cursor_pos = self.mapFromScene(scene_pos)
            delta = new_cursor_pos - cursor_pos.toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
        event.ignore()  # Allow default if blocked

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._user_interacted = True  # Mark as interacted (panning)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            ars_window = QApplication.instance().activeWindow() # This returns the main window instance
            ars_window.img.hide()
            ars_window.viewport.show()

            close_all_open_context_menus()

        super().keyPressEvent(event)

class ImageViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image_path = ""
        self.scene = QGraphicsScene()
        self.view = ImageViewer(self.scene, self)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.view)

    def fit_image(self, animated=False, duration=250):
        """Fit the image in the view, optionally with animation.
        
        Args:
            animated: If True, smoothly animate to the fit view.
            duration: Animation duration in milliseconds (default 250).
        """
        if self.view.image_rect is None:
            return
            
        if not animated:
            self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)
            return
        
        # Stop any existing fit animation
        if hasattr(self, '_fit_anim') and self._fit_anim.state() == QVariantAnimation.State.Running:
            self._fit_anim.stop()
        
        # Calculate target transform
        view_rect = self.view.viewport().rect()
        image_rect = self.view.image_rect
        
        # Calculate scale to fit image in view while keeping aspect ratio
        scale_x = view_rect.width() / image_rect.width()
        scale_y = view_rect.height() / image_rect.height()
        target_scale = min(scale_x, scale_y)
        
        # Get current transform values
        current_transform = self.view.transform()
        current_scale = current_transform.m11()
        
        # Get current and target center positions
        current_center = self.view.mapToScene(self.view.viewport().rect().center())
        target_center = image_rect.center()
        
        # Store start values
        self._fit_start_scale = current_scale
        self._fit_target_scale = target_scale
        self._fit_start_center = current_center
        self._fit_target_center = target_center
        
        # Create animation
        self._fit_anim = QVariantAnimation(self)
        self._fit_anim.setStartValue(0.0)
        self._fit_anim.setEndValue(1.0)
        self._fit_anim.setDuration(duration)
        self._fit_anim.valueChanged.connect(self._update_fit_animation)
        self._fit_anim.start()
    
    def _update_fit_animation(self, progress):
        """Update view transform during fit animation."""
        # Interpolate scale (use easing for smoother feel)
        eased = progress * (2 - progress)  # Ease out quad
        
        current_scale = self._fit_start_scale + (self._fit_target_scale - self._fit_start_scale) * eased
        
        # Interpolate center position
        current_x = self._fit_start_center.x() + (self._fit_target_center.x() - self._fit_start_center.x()) * eased
        current_y = self._fit_start_center.y() + (self._fit_target_center.y() - self._fit_start_center.y()) * eased
        
        # Reset and apply new transform
        self.view.resetTransform()
        self.view.scale(current_scale, current_scale)
        self.view.centerOn(QPointF(current_x, current_y))

    def open_image(self, file_path=None, layer = -1, auto_fit=True):
        if hasattr(self, 'anim') and self.anim.state() == QVariantAnimation.State.Running:
            self.anim.stop()
        
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff)")
        if file_path:
            self.current_image_path = file_path
            pixmap = None
            
            # Check if it's a multi-layer image (TIFF)
            if file_path.lower().endswith(('.tif', '.tiff')):
                try:
                    pil_image = Image.open(file_path)
                    
                    # Count total frames/layers
                    n_frames = getattr(pil_image, 'n_frames', 1)
                    
                    # Handle layer index
                    layer_index = layer
                    if layer_index == -1:
                        layer_index = n_frames - 1  # Last layer
                    elif layer_index >= n_frames:
                        layer_index = 0  # Default to first if out of range
                    
                    # Seek to the correct frame
                    pil_image.seek(layer_index)
                    
                    # Copy the current frame to avoid reference issues
                    selected_layer = pil_image.copy()
                    
                    # Convert PIL image to QPixmap
                    if selected_layer.mode == "RGBA":
                        data = selected_layer.tobytes("raw", "RGBA")
                        qimage = QImage(data, selected_layer.width, selected_layer.height, QImage.Format.Format_RGBA8888)
                    elif selected_layer.mode == "RGB":
                        data = selected_layer.tobytes("raw", "RGB")
                        qimage = QImage(data, selected_layer.width, selected_layer.height, QImage.Format.Format_RGB888)
                    else:
                        selected_layer = selected_layer.convert("RGBA")
                        data = selected_layer.tobytes("raw", "RGBA")
                        qimage = QImage(data, selected_layer.width, selected_layer.height, QImage.Format.Format_RGBA8888)
                    
                    pixmap = QPixmap.fromImage(qimage)
                except Exception as e:
                    print(f"Error loading TIFF layer: {e}")
                    pixmap = QPixmap(file_path)  # Fallback to default loading
            else:
                # Regular image loading
                pixmap = QPixmap(file_path)
            
            if pixmap is None or pixmap.isNull():
                return
            
            self.scene.clear()
            item = QGraphicsPixmapItem(pixmap)
            item.setPos(-pixmap.width() / 2, -pixmap.height() / 2)
            self.scene.addItem(item)
            padding = 500.0
            self.scene.setSceneRect(-padding - pixmap.width() / 2, -padding - pixmap.height() / 2, pixmap.width() + 2 * padding, pixmap.height() + 2 * padding)
            self.view.image_rect = item.sceneBoundingRect()
            if auto_fit:
                self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.view._user_interacted = False  # Reset flag on new load

    def clear_image(self):
        if not self.scene.items():
            self._finalize_clear()
            return

        self.anim = QVariantAnimation(self)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setDuration(200)  # Duration in milliseconds
        self.anim.valueChanged.connect(self._update_opacity)
        self.anim.finished.connect(self._finalize_clear)
        self.anim.start()

    def _update_opacity(self, value):
        for item in self.scene.items():
            item.setOpacity(value)

    def _finalize_clear(self):
        self.scene.clear()
        self.view.image_rect = None
        self.current_image_path = ""
        self.view._user_interacted = False

    def get_current_image_path(self):
        return self.current_image_path

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.view.image_rect and not self.view._user_interacted:
            # Auto-refit if no interaction (e.g., after resize)
            self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)

