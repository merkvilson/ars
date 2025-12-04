"""Simple C4D Bridge - receives window info via socket and controls main window"""
import socket
import threading
import json
import ctypes
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication

class C4DBridge(QObject):
    window_info = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.original_flags = main_window.windowFlags()
        self.running = False
        self.docked = False
        
        # Connect signals
        self.window_info.connect(self._on_info)
        self.connected.connect(self._on_connect)
        self.disconnected.connect(self._on_disconnect)
    
    def start(self):
        self.running = True
        threading.Thread(target=self._server, daemon=True).start()
    
    def stop(self):
        self.running = False
        self._restore()
    
    def _server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 19847))
        sock.listen(1)
        sock.settimeout(1)
        
        while self.running:
            try:
                client, _ = sock.accept()
                self.connected.emit()
                self._handle(client)
            except socket.timeout:
                continue
            except:
                break
        sock.close()
    
    def _handle(self, client):
        client.settimeout(1)
        buf = ""
        while self.running:
            try:
                data = client.recv(4096).decode()
                if not data:
                    break
                buf += data
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    if line.strip():
                        msg = json.loads(line)
                        if msg.get('type') == 'window_info':
                            self.window_info.emit(msg['data'])
            except socket.timeout:
                continue
            except:
                break
        client.close()
        self.disconnected.emit()
    
    def _scale(self):
        """Get DPI scale factor"""
        try:
            hdc = ctypes.windll.user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
            ctypes.windll.user32.ReleaseDC(0, hdc)
            win_scale = dpi / 96.0
        except:
            win_scale = 1.0
        screen = QApplication.primaryScreen()
        qt_dpr = screen.devicePixelRatio() if screen else 1.0
        return win_scale / qt_dpr if qt_dpr else 1.0
    
    def _on_info(self, info):
        if not self.docked:
            return
        s = self._scale()
        self.mw.move(int(info['x'] * s), int(info['y'] * s))
        self.mw.resize(int(info['width'] * s), int(info['height'] * s))
    
    def _on_connect(self):
        self.docked = True
        self.mw.hide()
        self.mw.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.mw.show()
    
    def _on_disconnect(self):
        self.docked = False
        self._restore()
    
    def _restore(self):
        self.mw.hide()
        self.mw.setWindowFlags(self.original_flags)
        self.mw.show()
