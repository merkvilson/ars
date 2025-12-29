import os

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from ars_3d_engine.viewport import ViewportWidget
from ars_cmds.core_cmds.define_hotkeys import define_hotkeys
from ars_cmds.core_cmds.distribute_bubbles import distribute_bubbles
from ars_cmds.core_cmds.drag_and_drop import dd_drag, dd_drop
from core.cursor_modifier import set_default_cursor
from core.render_data import RenderDataManager
from core.sound_manager import play_sound
from hotkeys.hotkey_manager import HotkeyManager
from ui.widgets.bubble_layout import FloatingBubblesManager
from ui.widgets.cursor_follower import CursorFollowerWidget
from ui.widgets.splitter_layout import SplitterOverlay
from ui.img_viewer import ImageViewerWidget
from prefs.pref_controller import prefsConfig
from gs_viewer.gs_widget import GaussianSplattingWidget
from ars_cmds.bubble_cmds.render_video import execute_cmd as open_timeline
from ars_cmds.top_row_cmds.top_row import execute_cmd as open_top_row

class MainWindow(QMainWindow):
    def __init__(self, splash=None):
        super().__init__()
        self.splash = splash
        if self.splash: self.splash.show_message("Initializing UI...")
        
        self.setWindowTitle("Airen Studio 2026 - Alpha Version 0.52")
        
        self.set_app_icon()

        self.radial_menu = None
        self.bubbles_overlay = None
        self.central_widget = None
        self.layout = None
        self.viewport = None
        self.img = None
        self.gs_viewer = None
        self._closing = False  # flag to prevent loop
        
        self._setup_ui()
        self._setup_extensions()
        set_default_cursor("cursor")

        self.prefs = prefsConfig()


        #render data
        self.steps = 25
        self.seed = 0
        self.prompt = "marble texture, high detail, 8k"


    def set_app_icon(self):
        icon_path = os.path.join("res", "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join("res", "icon.png")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            QApplication.setWindowIcon(icon)

    def execute_startup_commands(self):
        def startup_commands(self):
            self.set_app_icon() # Double try to ensure icon is applied in Task Manager
            self.bubbles_overlay.load_layout(os.path.join("saved_layouts", "bubble_layout.arsl"))
            define_hotkeys(self)
            self.viewport.grid.start_animation(duration=2)
            play_sound("startup3")
            open_timeline(self)
            open_top_row(self)
            
            from ars_cmds import startup_cmds

            # Final try after everything is settled
            QTimer.singleShot(2000, self.set_app_icon)


        QTimer.singleShot(100, lambda: startup_commands(self))

    def _setup_ui(self):
        if self.splash: self.splash.show_message("Setting up Viewport...")
        print("Setting up UI...")

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

        # Gaussian Splatting viewer
        self.gs_viewer = GaussianSplattingWidget(self)
        self.layout.addWidget(self.gs_viewer)
        self.gs_viewer.hide()  # start hidden

        # Initialize hotkey_manager
        self.hotkey_manager = HotkeyManager(self.viewport._canvas.native)

        # Floating bubbles overlay
        if self.splash: self.splash.show_message("Loading Bubbles...")
        self.bubbles_overlay = FloatingBubblesManager(parent=self.central_widget)
        self.bubbles_overlay.setGeometry(self.central_widget.rect())
        distribute_bubbles(self)
        self.bubbles_overlay.show()

        # Splitter overlay
        self.splitter_overlay = SplitterOverlay(parent=self.central_widget)
        self.splitter_overlay.setGeometry(self.central_widget.rect())
        self.splitter_overlay.show()

        # Render data manager
        self.render_manager = RenderDataManager(
            default_workflow_path=os.path.join("extensions","comfyui","workflow", "render.json")
        )

        # Cursor follower
        self.CF = CursorFollowerWidget(self.central_widget)

        # Run startup commands
        self.execute_startup_commands()

    def _setup_extensions(self):
        """Initialize optional extensions"""
        if self.splash: self.splash.show_message("Loading Extensions...")
        try:
            from extensions.cinema_4d.bridge import C4DBridge
            self.c4d_bridge = C4DBridge(self)
            self.c4d_bridge.start()
        except Exception as e:
            print(f"[C4D] {e}")

    def msg(self, text: str, auto_close: int = 1500):
        text = str(text)
        self.CF.UP(key="additional_text", value=text, auto_close = auto_close)

    def swap_widgets(self, widget = None):
        if widget:
            #check if widget is already visible
            if widget.isVisible():
                return
            self.viewport.hide()
            self.img.hide()
            self.gs_viewer.hide()
            widget.show()
            self.msg(f"{widget.__class__.__name__}", auto_close=1000)
            return

        if self.viewport.isVisible():
            self.viewport.hide()
            self.img.show()
            self.msg("Image Viewer", auto_close=1000)
        elif self.img.isVisible():
            self.img.hide()
            self.gs_viewer.show()
            self.msg("Gaussian Splatting Viewer", auto_close=1000)
        else:
            self.gs_viewer.hide()
            self.viewport.show()
            self.msg("3D Viewport", auto_close=1000)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.bubbles_overlay: # Make the overlay always cover the central widget
            self.bubbles_overlay.setGeometry(self.centralWidget().rect())
            self.bubbles_overlay.reinitialize_bubbles()
        
        if self.splitter_overlay:
            self.splitter_overlay.setGeometry(self.centralWidget().rect())

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
            if hasattr(self, 'c4d_bridge'):
                self.c4d_bridge.stop(restore=False)
            
            # Stop video loop timer if it exists (from render_video bubble)
            if hasattr(self, '_loop_timer') and self._loop_timer:
                self._loop_timer.stop()
                self._loop_timer.deleteLater() #TODO: Find more events that needs cleanup

            # Stop render timer if it exists (from generate_render)
            if hasattr(self, '_render_timer') and self._render_timer:
                self._render_timer.stop()
                self._render_timer.deleteLater()

            # Close Vispy canvas to ensure its threads/resources are released
            if hasattr(self, 'viewport') and self.viewport and hasattr(self.viewport, '_canvas'):
                self.viewport._canvas.close()

            event.accept()
            QApplication.instance().quit()