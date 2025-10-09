import sys
import math

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QPointF, pyqtSignal, QRectF, pyqtProperty, QParallelAnimationGroup
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QPainterPath, QCursor
from PyQt6.QtWidgets import QWidget, QApplication, QCheckBox

import theme.fonts.new_fonts as RRRFONT

import json
import os
from core.sound_manager import play_sound

class BubbleConfig:
    """Configuration class for bubble parameters"""
    def __init__(self):
        self.symbol = ""
        self.color = QColor(100, 100, 100, 100)
        self.callbackL = lambda: print("left clicked")
        self.callbackR = lambda: print("right clicked")
        self.callbackM = lambda: print("middle clicked")
        self.radius = 22
        self.symbol_color = QColor(255, 255, 255, 220)
        self.font = RRRFONT.get_font(20)

class BubbleWidget(QWidget):
    bubble_moved = pyqtSignal(object)

    def __init__(self, config: BubbleConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.base_radius = config.radius
        self.max_scale = 1.2
        self.current_scale = 1.0
        self.is_dragging = False
        self.grid_position = QPoint()
        self.drag_start = QPoint()
        self.locked = True

        self.update_size()

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scale)
        self.timer.start(16)

        # --- Ripple state (kept minimal to avoid side effects) ---
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self.ripple_center = QPoint(self.width() // 2, self.height() // 2)
        self.ripple_end_radius = self.base_radius * 1.5
        self.ripple_anim_group = None

        # --- Flash overlay (independent of hover color) ---
        self._flash = 0.0  # 0..1

    # ---------- Animatable properties ----------
    @pyqtProperty(float)
    def ripple_radius(self):
        return self._ripple_radius

    @ripple_radius.setter
    def ripple_radius(self, value):
        self._ripple_radius = float(value)
        self.update()

    @pyqtProperty(float)
    def ripple_opacity(self):
        return self._ripple_opacity

    @ripple_opacity.setter
    def ripple_opacity(self, value):
        self._ripple_opacity = float(value)
        self.update()

    @pyqtProperty(float)
    def flash(self):
        return self._flash

    @flash.setter
    def flash(self, value):
        self._flash = float(value)
        self.update()
    # --------------------------------------------

    def update_size(self):
        size = int(self.base_radius * self.max_scale * 2)
        self.setFixedSize(size, size)

    def get_center_offset(self) -> int:
        return self.width() // 2

    def update_config(self, config: BubbleConfig):
        self.config = config
        self.base_radius = config.radius
        self.update_size()
        self.update()

    def enterEvent(self, event):
        play_sound("hover")
        if self.locked:
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.locked:
            self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Compute scale based on hover state (no timer needed in locked mode)
        self.current_scale = 1.1 if self.underMouse() else 1.0 if self.locked else self.current_scale
        radius_f = self.base_radius * self.current_scale
        center_f = self.width() / 2.0

        # Glow effect only in unlocked mode
        if not self.locked:
            painter.save()
            glow_color = QColor(255, 255, 255, 80)  # Subtle white glow
            glow_radius = radius_f * 1.1  # Slightly larger than bubble
            glow_path = QPainterPath()
            glow_path.addEllipse(QRectF(center_f - glow_radius, center_f - glow_radius, glow_radius * 2, glow_radius * 2))
            painter.fillPath(glow_path, QBrush(glow_color))
            painter.restore()

        # Apply hover effect (brighten color) in both locked and unlocked modes
        base_color = QColor(self.config.color)
        brush_color = base_color.lighter(255) if self.underMouse() else base_color

        # Bubble body
        path = QPainterPath()
        path.addEllipse(QRectF(center_f - radius_f, center_f - radius_f, radius_f * 2, radius_f * 2))
        painter.fillPath(path, brush_color)

        # Ripple (clipped inside bubble)
        if self._ripple_opacity > 0.0:
            painter.save()
            painter.setClipPath(path)
            ripple_color = QColor(255, 255, 255, int(255 * self._ripple_opacity * 0.6))
            painter.setBrush(QBrush(ripple_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(self.ripple_center), float(self._ripple_radius), float(self._ripple_radius))
            painter.restore()

        # Flash overlay
        if self._flash > 0.0:
            painter.save()
            flash_color = QColor(255, 255, 255, int(90 * self._flash))
            painter.setBrush(QBrush(flash_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.fillPath(path, flash_color)
            painter.restore()

        # symbol
        if self.config.symbol:
            painter.setPen(QPen(self.config.symbol_color))
            painter.setFont(self.config.font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.config.symbol)

    def update_scale(self):
        # Only used in unlocked mode
        target = 1.2 if self.is_dragging else (1.1 if self.underMouse() else 1.0)
        self.current_scale += (target - self.current_scale) * 0.15
        self.update()

    def hit_test(self, pos):
        center = QPoint(int(self.width() / 2), int(self.height() / 2))
        radius = self.base_radius * self.current_scale
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        return (dx*dx + dy*dy) <= radius*radius

    def mousePressEvent(self, event):
        if self.hit_test(event.position().toPoint()):
            if event.button() == Qt.MouseButton.LeftButton and not self.locked:
                self.is_dragging = True
                self.drag_start = event.globalPosition().toPoint() - self.pos()
                self.raise_()
            else:
                self._trigger_click_effect(event.position().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_start)
            self.bubble_moved.emit(self)
        elif self.underMouse() or self.hit_test(event.position().toPoint()):
            self.update()  # Trigger repaint for hover effect
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        pos = event.position().toPoint()
        if self.hit_test(pos):
            if event.button() == Qt.MouseButton.LeftButton:
                if self.is_dragging:
                    self.is_dragging = False
                    self.bubble_moved.emit(self)
                elif self.locked and self.config.callbackL:
                    self.config.callbackL()
            elif event.button() == Qt.MouseButton.RightButton and self.config.callbackR:
                self.config.callbackR()
            elif event.button() == Qt.MouseButton.MiddleButton and self.config.callbackM:
                self.config.callbackM()
        super().mouseReleaseEvent(event)

    def _trigger_click_effect(self, pos: QPoint):
        self.ripple_center = pos
        self.ripple_end_radius = self.base_radius * self.current_scale * 1.5

        if self.ripple_anim_group:
            self.ripple_anim_group.stop()

        self.ripple_anim_group = QParallelAnimationGroup(self)

        radius_anim = QPropertyAnimation(self, b"ripple_radius")
        radius_anim.setDuration(400)
        radius_anim.setStartValue(0.0)
        radius_anim.setEndValue(self.ripple_end_radius)
        radius_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        opacity_anim = QPropertyAnimation(self, b"ripple_opacity")
        opacity_anim.setDuration(400)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        flash_anim = QPropertyAnimation(self, b"flash")
        flash_anim.setDuration(400)
        flash_anim.setStartValue(0.0)
        flash_anim.setKeyValueAt(0.15, 1.0)
        flash_anim.setEndValue(0.0)
        flash_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.ripple_anim_group.addAnimation(radius_anim)
        self.ripple_anim_group.addAnimation(opacity_anim)
        self.ripple_anim_group.addAnimation(flash_anim)
        self.ripple_anim_group.finished.connect(self._reset_ripple)
        self.ripple_anim_group.start()

    def _reset_ripple(self):
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self._flash = 0.0
        self.update()

    def animate_to(self, pos: QPoint):
        self.animation.stop()
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(pos)
        self.animation.start()

    def set_locked(self, locked: bool):
        self.locked = locked
        if locked:
            self.timer.stop()  # Stop timer in locked mode
            self.current_scale = 1.0 if not self.underMouse() else 1.1
            self.update()
        else:
            self.timer.start(16)  # Restart timer in unlocked mode
            self.update()

class FloatingBubblesManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bubbles = []
        self.bubbles_initialized = False
        self.grid_spacing = 45
        self.grid_offset = 45
        self.show_grid = True
        self.grid_occupancy = {}
        self.locked = True  # editing disabled by default

        self.clusters = []
        self.cluster_distance = 90

        self.dragging_cluster = None
        self.cluster_drag_start = QPoint()
        self.cluster_offsets = {}

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self.update)
        self.cursor_timer.start(16)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reinitialize_bubbles()

    def toggle_lock(self, state):
        self.locked = state == Qt.CheckState.Checked.value
        for bubble in self.bubbles:
            bubble.set_locked(self.locked)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, self.locked)
        if self.locked:
            self.cursor_timer.stop()  # Stop cursor timer in locked mode
        else:
            self.cursor_timer.start(16)  # Restart in unlocked mode
        self.update()

    def is_dragging(self) -> bool:
        return any(b.is_dragging for b in self.bubbles) or self.dragging_cluster is not None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw clusters
        for cluster in self.clusters:
            if len(cluster) < 2:
                continue
            min_x = min(b.x() for b in cluster)
            min_y = min(b.y() for b in cluster)
            max_x = max(b.x() + b.width() for b in cluster)
            max_y = max(b.y() + b.height() for b in cluster)

            # Skip glow in locked mode
            if not self.locked:
                painter.save()
                glow_color = QColor(255, 255, 255, 40)
                glow_rect = QRectF(min_x - 10, min_y - 10,
                                   (max_x - min_x) + 20, (max_y - min_y) + 20)
                painter.setBrush(QBrush(glow_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(glow_rect, 24, 24)
                painter.restore()

            # Cluster body
            rect = QRectF(min_x - 8, min_y - 8,  
                          (max_x - min_x) + 13, (max_y - min_y) + 13)
            painter.setBrush(QBrush(QColor(250, 250, 250, 10)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 20, 20)

        # Skip grid drawing in locked mode
        if not self.locked and self.show_grid and self.is_dragging():
            painter.setPen(Qt.PenStyle.NoPen)
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            max_dist = 150
            y = self.grid_offset
            while y < self.height():
                x = self.grid_offset
                while x < self.width():
                    dist = math.hypot(cursor_pos.x() - x, cursor_pos.y() - y)
                    alpha = max(0, 255 - int((dist / max_dist) * 255))
                    if alpha > 0:
                        painter.setBrush(QColor(255, 255, 255, alpha))
                        painter.drawEllipse(x - 2, y - 2, 4, 4)
                    x += self.grid_spacing
                y += self.grid_spacing

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.locked:
            click = event.position().toPoint()
            for cluster in self.clusters:
                if len(cluster) < 2:
                    continue
                min_x = min(b.x() for b in cluster) - 20
                min_y = min(b.y() for b in cluster) - 20
                max_x = max(b.x() + b.width() for b in cluster) + 20
                max_y = max(b.y() + b.height() for b in cluster) + 20
                rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

                if rect.contains(click.toPointF()):
                    self.dragging_cluster = cluster
                    self.cluster_drag_start = event.globalPosition().toPoint()
                    self.cluster_offsets = {
                        b: b.pos() - self.cluster_drag_start for b in cluster
                    }
                    event.accept()
                    return
        event.ignore()

    def mouseMoveEvent(self, event):
        if self.dragging_cluster and event.buttons() & Qt.MouseButton.LeftButton:
            new_global = event.globalPosition().toPoint()
            for b in self.dragging_cluster:
                b.move(self.cluster_offsets[b] + new_global)
            self.update_clusters()
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging_cluster:
            for b in self.dragging_cluster:
                old_pos = b.grid_position
                if (old_pos.x(), old_pos.y()) in self.grid_occupancy and self.grid_occupancy[(old_pos.x(), old_pos.y())] == b:
                    del self.grid_occupancy[(old_pos.x(), old_pos.y())]

                desired_x, desired_y = self.screen_to_grid(b.pos(), b.get_center_offset())
                final_x, final_y = self.find_free_grid(desired_x, desired_y, b)

                self.grid_occupancy[(final_x, final_y)] = b
                b.grid_position = QPoint(final_x, final_y)

                target = self.grid_to_screen(final_x, final_y)
                b.animate_to(QPoint(target.x() - b.get_center_offset(),
                                    target.y() - b.get_center_offset()))

            self.dragging_cluster = None
            self.cluster_offsets.clear()
            self.update_clusters()
            event.accept()
        else:
            event.ignore()

    def update_clusters(self):
        visited = set()
        clusters = []

        def bfs(start):
            q = [start]
            cluster = []
            while q:
                b = q.pop()
                if b in visited:
                    continue
                visited.add(b)
                cluster.append(b)
                for other in self.bubbles:
                    if other not in visited:
                        if self.distance(b, other) < self.cluster_distance:
                            q.append(other)
            return cluster

        for b in self.bubbles:
            if b not in visited:
                clusters.append(bfs(b))

        self.clusters = clusters
        self.update()

    def distance(self, b1: BubbleWidget, b2: BubbleWidget):
        c1 = b1.pos() + QPoint(b1.width() // 2, b1.height() // 2)
        c2 = b2.pos() + QPoint(b2.width() // 2, b2.height() // 2)
        return math.hypot(c1.x() - c2.x(), c1.y() - c2.y())

    def grid_to_screen(self, gx, gy) -> QPoint:
        return QPoint(self.grid_offset + gx * self.grid_spacing,
                      self.grid_offset + gy * self.grid_spacing)

    def screen_to_grid(self, pos: QPoint, center_offset: int) -> tuple:
        if center_offset <= 0:
            center_offset = 30
        gx = round((pos.x() + center_offset - self.grid_offset) / self.grid_spacing)
        gy = round((pos.y() + center_offset - self.grid_offset) / self.grid_spacing)
        max_gx = max(1, (self.width() - self.grid_offset) // self.grid_spacing)
        max_gy = max(1, (self.height() - self.grid_offset) // self.grid_spacing)
        return max(0, min(max_gx, gx)), max(0, min(max_gy, gy))

    def find_free_grid(self, pref_x, pref_y, exclude=None):
        if (pref_x, pref_y) not in self.grid_occupancy or self.grid_occupancy.get((pref_x, pref_y)) == exclude:
            return pref_x, pref_y

        max_gx = max(1, (self.width() - self.grid_offset) // self.grid_spacing)
        max_gy = max(1, (self.height() - self.grid_offset) // self.grid_spacing)
        max_dist = max(max_gx, max_gy)

        for dist in range(1, max_dist + 1):
            for dx in range(-dist, dist + 1):
                for dy in range(-dist, dist + 1):
                    if abs(dx) != dist and abs(dy) != dist:
                        continue
                    tx, ty = pref_x + dx, pref_y + dy
                    if (tx >= 0 and ty >= 0 and
                        tx <= max_gx and ty <= max_gy and
                        ((tx, ty) not in self.grid_occupancy or self.grid_occupancy.get((tx, ty)) == exclude)):
                        return tx, ty
        return pref_x, pref_y

    def handle_bubble_moved(self, bubble: BubbleWidget):
        if bubble.is_dragging:
            self.update_clusters()
            return

        old_pos = bubble.grid_position
        if (old_pos.x(), old_pos.y()) in self.grid_occupancy and self.grid_occupancy[(old_pos.x(), old_pos.y())] == bubble:
            del self.grid_occupancy[(old_pos.x(), old_pos.y())]

        desired_x, desired_y = self.screen_to_grid(bubble.pos(), bubble.get_center_offset())
        final_x, final_y = self.find_free_grid(desired_x, desired_y, bubble)

        self.grid_occupancy[(final_x, final_y)] = bubble
        bubble.grid_position = QPoint(final_x, final_y)

        target = self.grid_to_screen(final_x, final_y)
        bubble.animate_to(QPoint(target.x() - bubble.get_center_offset(),
                                target.y() - bubble.get_center_offset()))

        self.update_clusters()

    def get_preferred_grid(self):
        max_gx = max(1, (self.width() - self.grid_offset) // self.grid_spacing)
        max_gy = max(1, (self.height() - self.grid_offset) // self.grid_spacing)
        return max_gx // 2, max_gy // 2

    def position_bubble(self, bubble: BubbleWidget):
        pref_gx, pref_gy = self.get_preferred_grid()
        gx, gy = self.find_free_grid(pref_gx, pref_gy)
        pos = self.grid_to_screen(gx, gy)
        bubble.move(pos.x() - bubble.get_center_offset(), pos.y() - bubble.get_center_offset())
        bubble.grid_position = QPoint(gx, gy)
        self.grid_occupancy[(gx, gy)] = bubble
        bubble.show()
        bubble.raise_()
        self.update_clusters()

    def add_bubble(self, config: BubbleConfig = None) -> BubbleWidget:
        if config is None:
            config = BubbleConfig()
        parent_widget = self.parent() if self.parent() else self
        bubble = BubbleWidget(config, parent_widget)
        bubble.bubble_moved.connect(self.handle_bubble_moved)
        self.bubbles.append(bubble)
        if self.width() > 100 and self.height() > 100:
            self.position_bubble(bubble)
        if self.locked:
            bubble.set_locked(True)
        self.update_clusters()
        return bubble

    def remove_bubble(self, bubble: BubbleWidget):
        if bubble in self.bubbles:
            pos = bubble.grid_position
            if (pos.x(), pos.y()) in self.grid_occupancy:
                del self.grid_occupancy[(pos.x(), pos.y())]
            self.bubbles.remove(bubble)
            bubble.deleteLater()
            self.update_clusters()

    def reinitialize_bubbles(self):
        if hasattr(self, 'bubbles_initialized') and self.bubbles_initialized:
            return
        if self.width() < 200 or self.height() < 200:
            return
        self.grid_occupancy.clear()
        for bubble in self.bubbles:
            self.position_bubble(bubble)
        self.bubbles_initialized = True
        self.update_clusters()

    def save_layout(self, filename="bubble_layout.arsl"):
        """Save the current bubble positions to a JSON file."""
        layout = {
            "bubbles": [
                {
                    "symbol": bubble.config.symbol,
                    "grid_x": bubble.grid_position.x(),
                    "grid_y": bubble.grid_position.y()
                }
                for bubble in self.bubbles
            ]
        }
        with open(filename, 'w') as f:
            json.dump(layout, f, indent=4)

    def load_layout(self, filename="bubble_layout.arsl"):
        """Load bubble positions from a JSON file and apply them with animation."""
        try:
            with open(filename, 'r') as f:
                layout = json.load(f)
            
            self.grid_occupancy.clear()
            
            active_animations = []
            
            for bubble_data in layout.get("bubbles", []):
                symbol = bubble_data.get("symbol", "")
                grid_x = bubble_data.get("grid_x", 0)
                grid_y = bubble_data.get("grid_y", 0)
                
                for bubble in self.bubbles:
                    if bubble.config.symbol == symbol:
                        old_pos = bubble.grid_position
                        if (old_pos.x(), old_pos.y()) in self.grid_occupancy:
                            del self.grid_occupancy[(old_pos.x(), old_pos.y())]
                        
                        gx, gy = self.find_free_grid(grid_x, grid_y, bubble)
                        self.grid_occupancy[(gx, gy)] = bubble
                        bubble.grid_position = QPoint(gx, gy)
                        
                        target = self.grid_to_screen(gx, gy)
                        bubble.animation.stop()
                        bubble.animate_to(QPoint(target.x() - bubble.get_center_offset(),
                                               target.y() - bubble.get_center_offset()))
                        active_animations.append(bubble.animation)
                        break
            
            def on_animations_finished():
                nonlocal active_animations
                active_animations = [anim for anim in active_animations if anim.state() == QPropertyAnimation.State.Running]
                if not active_animations:
                    self.update_clusters()
                    self.update()
            
            for anim in active_animations:
                anim.finished.connect(on_animations_finished)
            
            for anim in active_animations:
                anim.start()
            
            if not active_animations:
                self.update_clusters()
                self.update()
        except FileNotFoundError:
            print(f"Layout file {filename} not found.")
        except json.JSONDecodeError:
            print(f"Invalid JSON format in {filename}.")