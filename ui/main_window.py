from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
import os

from ui.widgets.hierarchy_tree import ObjectHierarchyWindow
from ars_3d_engine.viewport import ViewportWidget
from ui.widgets.bubble_layout import FloatingBubblesManager
from core.render_data import RenderDataManager
from ui.widgets.cursor_follower import CursorFollowerWidget

from hotkeys.hotkey_manager import HotkeyManager
from ars_cmds.core_cmds.distribute_bubbles import distribute_bubbles
from ars_cmds.core_cmds.define_hotkeys import define_hotkeys
from ars_cmds.core_cmds.drag_and_drop import dd_drag, dd_drop

from .img_viewer import ImageViewerWidget
from core.cursor_modifier import set_default_cursor

from core.sound_manager import play_sound


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Airen Studio 2025")
        self.radial_menu = None
        self.bubbles_overlay = None
        self.central_widget = None
        self.layout = None
        self.viewport = None
        self.img = None
        self._closing = False  # flag to prevent loop

        self._setup_ui()
        set_default_cursor("cursor")



    def execute_startup_commands(self):
        def startup_commands(self):
            self.hierarchy.call_toggle_minimize()
            self.bubbles_overlay.load_layout(os.path.join("saved_layouts", "bubble_layout.arsl"))
            define_hotkeys(self)
            self.viewport.grid.start_animation(duration=2)
            play_sound("startup3")


        QTimer.singleShot(100, lambda: startup_commands(self))

    def _setup_ui(self):
        # Background widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Store layout as attribute
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Viewport
        self.viewport = ViewportWidget(self)
        self.viewport._canvas.native.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.layout.addWidget(self.viewport)

        # Image viewer
        self.img = ImageViewerWidget(self)
        self.layout.addWidget(self.img)
        self.img.hide()  # start hidden

        # Initialize hotkey_manager
        self.hotkey_manager = HotkeyManager(self.viewport._canvas.native)

        # Add hierarchy panel (top-right)
        self.hierarchy = ObjectHierarchyWindow(self.viewport)
        self.hierarchy.setParent(self.central_widget)
        self.hierarchy.show()
        #self.hierarchy.hide()

        # Floating bubbles overlay
        self.bubbles_overlay = FloatingBubblesManager(parent=self.central_widget)
        self.bubbles_overlay.setGeometry(self.central_widget.rect())
        distribute_bubbles(self)
        self.bubbles_overlay.show()

        # Render data manager
        self.render_manager = RenderDataManager(
            default_workflow_path=os.path.join("extensions","comfyui","workflow", "render.json")
        )

        # Cursor follower
        self.CF = CursorFollowerWidget(self.central_widget)

        # Run startup commands
        self.execute_startup_commands()



    def swap_widgets(self):
        if self.viewport.isVisible():
            self.viewport.hide()
            self.img.show()
        else:
            self.img.hide()
            self.viewport.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update hierarchy window position
        self.hierarchy.move(self.width() - self.hierarchy.width() - 5, 5)
        # Make the overlay always cover the central widget
        if self.bubbles_overlay:
            self.bubbles_overlay.setGeometry(self.centralWidget().rect())
            self.bubbles_overlay.reinitialize_bubbles()

    def showEvent(self, event):
        super().showEvent(event)
        if self.bubbles_overlay:
            self.bubbles_overlay.setGeometry(self.centralWidget().rect())
            self.bubbles_overlay.reinitialize_bubbles()

    def dragEnterEvent(self, event):
        dd_drag(self, event)

    def dropEvent(self, event):
        dd_drop(self, event)

    def closeEvent(self, event):
        if not self._closing:
            event.ignore()
            play_sound("exit")
            QTimer.singleShot(100, self.hide)
            self._closing = True
            QTimer.singleShot(3000, self.close)
        else:
            event.accept()