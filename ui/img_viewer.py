import math
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QWidget, QFileDialog
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QMouseEvent, QPen, QColor, QPainter, QBrush, QImage
from PyQt6.QtCore import Qt, QRectF, QPointF
from PIL import Image, ImageSequence

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
        major_spacing = 250
        minor_pen = QPen(QColor(80, 80, 80), 1.5 / zoom)
        major_pen = QPen(QColor(120, 120, 120), 2 / zoom)

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
            x_axis_pen = QPen(QColor.fromRgbF(0.9, 0.3, 0.3, 1), 2.5 / zoom)
            painter.setPen(x_axis_pen)
            painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))

        if rect.left() <= 0 <= rect.right():
            y_axis_pen = QPen(QColor.fromRgbF(0.3, 0.3, 0.9, 1), 2.5 / zoom)
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

class ImageViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.view = ImageViewer(self.scene, self)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.view)

    def fit_image(self):
        self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def open_image(self, file_path=None, layer = -1, auto_fit=True):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff)")
        if file_path:
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.view.image_rect and not self.view._user_interacted:
            # Auto-refit if no interaction (e.g., after resize)
            self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)

