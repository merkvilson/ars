from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl, QEvent
from PyQt6.QtGui import QColor


BBL_TEST_CONFIG = {"symbol": ic.ICON_TEST}
def BBL_TEST(*args):
    run_ext(__file__)
    
DEFAULT_URL = r"http://127.0.0.1:8188/"


class BrowserWindow(QMainWindow):
    def __init__(self, parent_window):
        super().__init__(None)
        self.parent_window = parent_window
        self._was_visible = False
        self._resizing = False
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.browser = QWebEngineView()
        self.browser.page().setBackgroundColor(QColor("#151515"))
        self.browser.setUrl(QUrl(DEFAULT_URL))
        self.setCentralWidget(self.browser)
        self.setStyleSheet("background-color: #151515;")
        
        # Install event filter on main window to track focus/minimize
        self.parent_window.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if obj == self.parent_window:
            if event.type() == QEvent.Type.WindowStateChange:
                if self.parent_window.isMinimized():
                    self._was_visible = self.isVisible()
                    self.hide()
                else:
                    if self._was_visible:
                        self.show()
                        self.raise_()
            elif event.type() == QEvent.Type.Hide:
                self._was_visible = self.isVisible()
                self.hide()
            elif event.type() == QEvent.Type.Show:
                if self._was_visible:
                    self.show()
                    self.raise_()
        
        return super().eventFilter(obj, event)
    
    def update_position(self, x, y, w, h):
        self._resizing = True
        self.setGeometry(x, y, w, h)
        self.show()
        self.raise_()
        self._resizing = False


_browser_window = None

def execute_cmd(ars_window):
    global _browser_window
    
    browser_height = getattr(ars_window.prefs, 'browser_height', 600)
    
    config = ContextMenuConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = False
    config.distribution_mode = "x"
    config.custom_height = browser_height
    config.custom_width = ars_window.width()
    config.extra_distance = [0, 99999]

    # Create browser window
    if _browser_window is None:
        _browser_window = BrowserWindow(ars_window)
    
    # Position browser below the control bar
    bar_height = 50
    main_pos = ars_window.mapToGlobal(ars_window.rect().topLeft())
    _browser_window.update_position(
        main_pos.x(),
        main_pos.y() + ars_window.height() - browser_height + bar_height,
        ars_window.width(),
        browser_height - bar_height
    )
    _browser_window.show()

    options_list = [
        [
            "   ",
            ic.ICON_ARROW_BARS_V,
        ],
        "   ",
    ]

    config.slider_values = {
        ic.ICON_ARROW_BARS_V: (55, ars_window.height() - 55 - 20, browser_height),
    }
    config.incremental_values = {
        ic.ICON_ARROW_BARS_V: (-20, "y"),
    }

    def resize_browser(value):
        ctx.resize_top(value)
        main_pos = ars_window.mapToGlobal(ars_window.rect().topLeft())
        _browser_window.update_position(
            main_pos.x(),
            main_pos.y() + ars_window.height() - int(value) + bar_height,
            ars_window.width(),
            int(value) - bar_height
        )

    def close_browser():
        global _browser_window
        if _browser_window:
            _browser_window.close()
            _browser_window = None
        ctx.close_animated()

    config.callbackL = {
        ic.ICON_ARROW_BARS_V: resize_browser,
    }
    
    config.callback_on_close = lambda: (_browser_window.hide() if _browser_window else None)

    ctx = open_context(
        items=options_list,
        config=config
    )
    return ctx

