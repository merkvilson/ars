from ui.widgets.context_menu import CtxConfig
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import subprocess
import sys
import ctypes
from PyQt6.QtCore import QObject, QEvent, QTimer

BBL_comfyui_node_editor_CONFIG = {"symbol": ic.ICON_TEST, "hidden": True}
def BBL_comfyui_node_editor(*args):
    run_ext(__file__)
    
DEFAULT_URL = r"http://127.0.0.1:8188/"

class BrowserManager(QObject):
    def __init__(self, ars_window):
        super().__init__(ars_window)
        self.ars_window = ars_window
        self.process = None
        self.ars_window.installEventFilter(self)
        self._hwnd = None
        self.target_rect = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_window_and_move)
        self.timer.setInterval(50)

    def _get_hwnd(self):
        if self._hwnd and ctypes.windll.user32.IsWindow(self._hwnd):
            return self._hwnd
        self._hwnd = ctypes.windll.user32.FindWindowW(None, "ComfyUI")
        return self._hwnd

    def eventFilter(self, obj, event):
        if obj == self.ars_window:
            if event.type() == QEvent.Type.WindowStateChange:
                if self.ars_window.isMinimized():
                    self.set_visibility(False)
                else:
                    self.set_visibility(True)
            elif event.type() == QEvent.Type.Close:
                self.close_browser()
        return super().eventFilter(obj, event)

    def set_visibility(self, visible):
        hwnd = self._get_hwnd()
        if hwnd:
            # SW_MINIMIZE = 6, SW_RESTORE = 9
            cmd = 9 if visible else 6
            ctypes.windll.user32.ShowWindow(hwnd, cmd)

    def update_geometry(self, x, y, w, h):
        hwnd = self._get_hwnd()
        if hwnd:
            ctypes.windll.user32.MoveWindow(hwnd, int(x), int(y), int(w), int(h), True)
            return True
        return False

    def check_window_and_move(self):
        hwnd = self._get_hwnd()
        if hwnd and self.target_rect:
            x, y, w, h = self.target_rect
            
            # Set owner to main window to handle Z-order automatically
            # GWL_HWNDPARENT = -8
            try:
                main_hwnd = int(self.ars_window.winId())
                ctypes.windll.user32.SetWindowLongPtrW(hwnd, -8, main_hwnd)
            except:
                # Fallback for 32-bit python if needed
                try:
                    ctypes.windll.user32.SetWindowLongW(hwnd, -8, main_hwnd)
                except:
                    pass
            
            # Hide from taskbar: Add WS_EX_TOOLWINDOW and remove WS_EX_APPWINDOW
            try:
                GWL_EXSTYLE = -20
                WS_EX_TOOLWINDOW = 0x00000080
                WS_EX_APPWINDOW = 0x00040000
                
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            except:
                pass
            
            ctypes.windll.user32.MoveWindow(hwnd, int(x), int(y), int(w), int(h), True)
            self.timer.stop()

    def show_browser(self, x, y, w, h):
        self.target_rect = (x, y, w, h)
        
        # If process exists and window is found, just move it
        if self.process and self.process.poll() is None:
            if self.update_geometry(x, y, w, h):
                self.set_visibility(True)
                return

        # Kill existing if any (zombie or lost window)
        self.close_browser()
        
        # We pass coordinates to create_window, but we also enforce them with MoveWindow via timer
        # to ensure correct physical positioning regardless of pywebview's DPI handling.
        # Removed on_top=True to avoid covering other applications.
        # Z-order is handled by setting owner window in check_window_and_move.
        script = f'''
import webview
import sys
window = webview.create_window(
    'ComfyUI',
    '{DEFAULT_URL}',
    x={int(x)}, y={int(y)}, width={int(w)}, height={int(h)},
    frameless=True,
    easy_drag=False,
    on_top=False,
    background_color='#151515'
)
webview.start()
'''
        self.process = subprocess.Popen(
            [sys.executable, '-c', script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.timer.start()

    def close_browser(self):
        self.timer.stop()
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
            self.process = None
        self._hwnd = None

_manager = None

def execute_cmd(ars_window):
    global _manager
    if _manager is None:
        _manager = BrowserManager(ars_window)
    
    browser_height = getattr(ars_window.prefs, 'browser_height', 600)
    scale_factor = ars_window.devicePixelRatio()
    
    config = CtxConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = False
    config.distribution_mode = "x"
    config.custom_height = browser_height
    config.custom_width = ars_window.width()
    config.extra_distance = [0, 99999]

    bar_height = 50
    main_pos = ars_window.mapToGlobal(ars_window.rect().topLeft())
    
    _manager.show_browser(
        main_pos.x() * scale_factor,
        (main_pos.y() + ars_window.height() - browser_height + bar_height) * scale_factor,
        ars_window.width() * scale_factor,
        (browser_height - bar_height) * scale_factor
    )

    options_list = [
        [
            ic.ICON_ARROW_BARS_V,
            ic.ICON_TXT_SIZE,
            ic.ICON_SHADER_SMOOTH,
            "   ",
            "   ",
            ic.ICON_PLAYER_PLAY,
            ic.ICON_POWER,
            ic.ICON_PLAYER_STOP,
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
        
        # Try to update geometry directly first
        success = _manager.update_geometry(
            main_pos.x() * scale_factor,
            (main_pos.y() + ars_window.height() - int(value) + bar_height) * scale_factor,
            ars_window.width() * scale_factor,
            (int(value) - bar_height) * scale_factor
        )

    config.callbackL = {
        ic.ICON_ARROW_BARS_V: resize_browser,
    }
    
    config.callback_on_close = _manager.close_browser

    ctx = config.open_context(items=options_list)
    return ctx

