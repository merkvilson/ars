import sys
import math
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QWidget, QFileDialog, QGraphicsRectItem, QGraphicsItem
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QMouseEvent, QPen, QColor, QPainter, QBrush, QAction, QShowEvent
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF

class ViewportRectItem(QGraphicsRectItem):
    def __init__(self, minimap_view):
        super().__init__()
        self.minimap_view = minimap_view
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            width = self.rect().width()
            height = self.rect().height()
            scene_rect = self.scene().sceneRect()
            min_x = scene_rect.left()
            max_x = scene_rect.right() - width
            min_y = scene_rect.top()
            max_y = scene_rect.bottom() - height
            new_pos.setX(max(min_x, min(new_pos.x(), max_x)))
            new_pos.setY(max(min_y, min(new_pos.y(), max_y)))
            return new_pos
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.scene():
            if not self.minimap_view._updating_rect:
                center = self.pos() + QPointF(self.rect().width() / 2, self.rect().height() / 2)
                self.minimap_view.parent_view.centerOn(center)
                self.minimap_view.update_viewport_rect()
        return super().itemChange(change, value)

class MinimapView(QGraphicsView):
    def __init__(self, parent_view, main_pixmap):
        super().__init__()
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.parent_view = parent_view
        self.main_pixmap = main_pixmap
        self.minimap_scene = QGraphicsScene(self)
        self.setScene(self.minimap_scene)
        self.setFixedSize(150, 150)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._updating_rect = False
        self.setBackgroundBrush(QBrush(Qt.BrushStyle.NoBrush))

        if self.main_pixmap:
            self.minimap_pixmap = QGraphicsPixmapItem(self.main_pixmap)
            self.minimap_pixmap.setPos(-self.main_pixmap.width() / 2, -self.main_pixmap.height() / 2)
            self.minimap_scene.addItem(self.minimap_pixmap)
            self.minimap_scene.setSceneRect(self.minimap_pixmap.sceneBoundingRect())

        self.viewport_rect = ViewportRectItem(self)
        self.viewport_rect.setPen(QPen(QColor(255, 255, 255, 100)))
        self.viewport_rect.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.viewport_rect.setZValue(10)
        self.minimap_scene.addItem(self.viewport_rect)

        self.left_overlay = QGraphicsRectItem()
        self.left_overlay.setZValue(5)
        self.left_overlay.setBrush(QBrush(QColor(0, 0, 0, 100)))
        self.left_overlay.setPen(QPen(Qt.PenStyle.NoPen))
        self.minimap_scene.addItem(self.left_overlay)

        self.right_overlay = QGraphicsRectItem()
        self.right_overlay.setZValue(5)
        self.right_overlay.setBrush(QBrush(QColor(0, 0, 0, 100)))
        self.right_overlay.setPen(QPen(Qt.PenStyle.NoPen))
        self.minimap_scene.addItem(self.right_overlay)

        self.top_overlay = QGraphicsRectItem()
        self.top_overlay.setZValue(5)
        self.top_overlay.setBrush(QBrush(QColor(0, 0, 0, 100)))
        self.top_overlay.setPen(QPen(Qt.PenStyle.NoPen))
        self.minimap_scene.addItem(self.top_overlay)

        self.bottom_overlay = QGraphicsRectItem()
        self.bottom_overlay.setZValue(5)
        self.bottom_overlay.setBrush(QBrush(QColor(0, 0, 0, 100)))
        self.bottom_overlay.setPen(QPen(Qt.PenStyle.NoPen))
        self.minimap_scene.addItem(self.bottom_overlay)

        self.update_viewport_rect()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        if self.scene():
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def update_viewport_rect(self):
        if self._updating_rect:
            return
        if not self.scene() or not self.parent_view or not self.main_pixmap:
            return
        self._updating_rect = True
        try:
            transform = self.parent_view.transform()
            viewport = self.parent_view.viewport().rect()
            top_left = self.parent_view.mapToScene(viewport.topLeft())
            bottom_right = self.parent_view.mapToScene(viewport.bottomRight())
            image_rect = self.minimap_pixmap.sceneBoundingRect()
            
            rect = QRectF(top_left, bottom_right)
            
            clamped_left = max(image_rect.left(), min(rect.left(), image_rect.right()))
            clamped_top = max(image_rect.top(), min(rect.top(), image_rect.bottom()))
            clamped_right = max(image_rect.left(), min(rect.right(), image_rect.right()))
            clamped_bottom = max(image_rect.top(), min(rect.bottom(), image_rect.bottom()))
            
            clamped_width = max(0, clamped_right - clamped_left)
            clamped_height = max(0, clamped_bottom - clamped_top)
            
            self.viewport_rect.setPos(clamped_left, clamped_top)
            self.viewport_rect.setRect(0, 0, clamped_width, clamped_height)

            image_left = image_rect.left()
            image_top = image_rect.top()
            image_right = image_rect.right()
            image_bottom = image_rect.bottom()
            image_width = image_rect.width()
            image_height = image_rect.height()

            # Update overlays without overlap
            left_w = max(0.0, clamped_left - image_left)
            self.left_overlay.setRect(QRectF(image_left, image_top, left_w, image_height))

            right_w = max(0.0, image_right - clamped_right)
            self.right_overlay.setRect(QRectF(clamped_right, image_top, right_w, image_height))

            top_h = max(0.0, clamped_top - image_top)
            self.top_overlay.setRect(QRectF(clamped_left, image_top, clamped_width, top_h))

            bottom_h = max(0.0, image_bottom - clamped_bottom)
            self.bottom_overlay.setRect(QRectF(clamped_left, clamped_bottom, clamped_width, bottom_h))
            
        finally:
            self._updating_rect = False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item != self.viewport_rect:
                scene_pos = self.mapToScene(event.pos())
                self.parent_view.centerOn(scene_pos)
                self.update_viewport_rect()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if event.buttons() & Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item != self.viewport_rect:
                scene_pos = self.mapToScene(event.pos())
                self.parent_view.centerOn(scene_pos)
                self.update_viewport_rect()

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
        self.minimap = None
        self.min_zoom = 1  # Lowered to allow zoom from small initial scales
        self.max_zoom = 10.0
        self.setBackgroundBrush(QBrush(QColor(45, 46, 50, 255)))
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

    def is_image_fully_visible(self):
        if not self.image_rect:
            return True
        viewport_rect = self.viewport().rect()
        top_left = self.mapToScene(viewport_rect.topLeft())
        bottom_right = self.mapToScene(viewport_rect.bottomRight())
        visible_rect = QRectF(top_left, bottom_right)
        return visible_rect.contains(self.image_rect)

    def update_minimap_visibility(self):
        if self.minimap and self.minimap_container:
            if self.is_image_fully_visible():
                self.minimap_container.hide()
            else:
                self.minimap_container.show()

    def wheelEvent(self, event: QWheelEvent):
        factor = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
        current_zoom = self.transform().m11()
        new_zoom = current_zoom * factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self._user_interacted = True  # Mark as interacted
            cursor_pos = event.position()
            scene_pos = self.mapToScene(cursor_pos.toPoint())
            self.scale(factor, factor)
            self.centerOn(scene_pos)
            new_cursor_pos = self.mapFromScene(scene_pos)
            delta = new_cursor_pos - cursor_pos.toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
            if self.minimap:
                self.minimap.update_viewport_rect()
            self.update_minimap_visibility()
        event.ignore()  # Allow default if blocked

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if self.minimap and event.buttons() & Qt.MouseButton.LeftButton:
            self._user_interacted = True  # Mark as interacted (panning)
            self.minimap.update_viewport_rect()
            self.update_minimap_visibility()

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        if self.minimap:
            self.minimap.update_viewport_rect()
            self.update_minimap_visibility()

class ImageViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.view = ImageViewer(self.scene, self)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.view)

        self.minimap_container = QWidget(self.view)
        self.view.minimap_container = self.minimap_container
        self.minimap_container.setStyleSheet("background: transparent; border: none;")
        self.minimap_container.setFixedSize(150, 150)
        self.minimap_layout = QVBoxLayout(self.minimap_container)
        self.minimap_layout.setContentsMargins(0, 0, 0, 0)
        self.minimap_container.hide()

    def fit_image(self):
        self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def open_image(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                return
            self.scene.clear()
            item = QGraphicsPixmapItem(pixmap)
            item.setPos(-pixmap.width() / 2, -pixmap.height() / 2)
            self.scene.addItem(item)
            padding = 500.0
            self.scene.setSceneRect(-padding - pixmap.width() / 2, -padding - pixmap.height() / 2, pixmap.width() + 2 * padding, pixmap.height() + 2 * padding)
            self.view.image_rect = item.sceneBoundingRect()
            #self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.view._user_interacted = False  # Reset flag on new load

            if self.view.minimap:
                self.minimap_layout.removeWidget(self.view.minimap)
                self.view.minimap.deleteLater()
            self.view.minimap = MinimapView(self.view, pixmap)
            self.minimap_layout.addWidget(self.view.minimap)
            self.view.minimap.update_viewport_rect()

            self.position_minimap()
            self.view.update_minimap_visibility()

    def position_minimap(self):
        self.minimap_container.move(
            10,
            self.view.viewport().height() - self.minimap_container.height() - 10
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.view.image_rect and not self.view._user_interacted:
            # Auto-refit if no interaction (e.g., after resize)
            #self.view.fitInView(self.view.image_rect, Qt.AspectRatioMode.KeepAspectRatio)
            if self.view.minimap:
                self.view.minimap.update_viewport_rect()
        self.position_minimap()
        if self.view.minimap:
            self.view.minimap.update_viewport_rect()
            self.view.update_minimap_visibility()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = ImageViewerWidget()
    widget.open_image()  # Optional: auto-open dialog
    widget.show()
    sys.exit(app.exec())