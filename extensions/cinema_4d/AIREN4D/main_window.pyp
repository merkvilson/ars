import c4d
import os
import socket
import json
import threading
import time

PLUGIN_ID = 1063060

class Client:
    def __init__(self):
        self.sock = None
        self.connected = False
        self.running = False
        self.pending = None
        self.last = {}
    
    def start(self):
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
    
    def stop(self):
        self.running = False
        if self.sock:
            try: self.sock.close()
            except: pass
    
    def _loop(self):
        while self.running:
            if not self.connected:
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.settimeout(1)
                    self.sock.connect(('127.0.0.1', 19847))
                    self.connected = True
                except:
                    self.sock = None
                    time.sleep(2)
                    continue
            if self.pending and self.pending != self.last:
                try:
                    self.sock.sendall((json.dumps({'type': 'window_info', 'data': self.pending}) + '\n').encode())
                    self.last = self.pending
                except:
                    self.connected = False
                    self.sock = None
            time.sleep(0.05)
    
    def send(self, x, y, w, h):
        self.pending = {'x': x, 'y': y, 'width': w, 'height': h}

client = Client()

class Area(c4d.gui.GeUserArea):
    def DrawMsg(self, x1, y1, x2, y2, msg):
        w, h = self.GetWidth(), self.GetHeight()
        pos = self.Local2Screen()
        px = pos.get('x', 0) if isinstance(pos, dict) else 0
        py = pos.get('y', 0) if isinstance(pos, dict) else 0
        client.send(px, py, w, h)
        
        self.DrawSetPen(c4d.Vector(0.2, 0.2, 0.2))
        self.DrawRectangle(x1, y1, x2, y2)
        self.DrawSetTextCol(c4d.Vector(0, 1, 0) if client.connected else c4d.Vector(1, 0.5, 0), c4d.Vector(0, 0, 0))
        self.DrawText(f"ARS: {'Connected' if client.connected else 'Waiting...'}", 10, 10)

class Dialog(c4d.gui.GeDialog):
    def CreateLayout(self):
        self.SetTitle("ARS Bridge")
        self.area = Area()
        self.AddUserArea(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 200, 40)
        self.AttachUserArea(self.area, 1000)
        return True
    
    def InitValues(self):
        self.SetTimer(200)
        client.start()
        return True
    
    def Timer(self, msg):
        self.area.Redraw()
    
    def DestroyWindow(self):
        client.stop()

class Command(c4d.plugins.CommandData):
    dialog = None
    def Execute(self, doc):
        if not self.dialog:
            self.dialog = Dialog()
        self.dialog.Open(c4d.DLG_TYPE_ASYNC, PLUGIN_ID, defaultw=200, defaulth=40)
        return True

if __name__ == "__main__":
    bmp = c4d.bitmaps.BaseBitmap()
    bmp.InitWith(os.path.join(os.path.dirname(__file__), "res", "render.png"))
    c4d.plugins.RegisterCommandPlugin(PLUGIN_ID, "ARS Bridge", 0, bmp, "Connect to ARS", Command())
