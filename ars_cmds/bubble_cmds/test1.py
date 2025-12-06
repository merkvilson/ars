from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic
from ars_cmds.core_cmds.run_ext import run_ext
import subprocess
import sys
import socket
import threading
import json


BBL_TEST_CONFIG = {"symbol": ic.ICON_TEST}
def BBL_TEST(*args):
    run_ext(__file__)
    
DEFAULT_URL = r"http://127.0.0.1:8188/"

# Browser controller class
class BrowserController:
    def __init__(self):
        self.process = None
        self.sock = None
        self.port = 19283
        
    def start(self, url=DEFAULT_URL, width=1200, height=800, title="ARS Browser"):
        code = f'''
import webview
import socket
import threading
import json

class JsonApi:
    def __init__(self, window):
        self.window = window
        self.running = True
        
    def handle_commands(self, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", port))
        server.listen(1)
        server.settimeout(1)
        
        while self.running:
            try:
                conn, addr = server.accept()
                data = conn.recv(4096).decode()
                if data:
                    cmd = json.loads(data)
                    result = self.execute(cmd)
                    conn.send(json.dumps(result).encode())
                conn.close()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error: {{e}}")
        server.close()
    
    def execute(self, cmd):
        action = cmd.get("action")
        try:
            if action == "navigate":
                self.window.load_url(cmd["url"])
            elif action == "resize":
                self.window.resize(cmd["width"], cmd["height"])
            elif action == "set_title":
                self.window.set_title(cmd["title"])
            elif action == "fullscreen":
                self.window.toggle_fullscreen()
            elif action == "minimize":
                self.window.minimize()
            elif action == "get_url":
                return {{"url": self.window.get_current_url()}}
            elif action == "close":
                self.running = False
                self.window.destroy()
            return {{"ok": True}}
        except Exception as e:
            return {{"error": str(e)}}

def on_closed():
    api.running = False

window = webview.create_window(
    "{title}",
    "{url}",
    width={width},
    height={height},
    resizable=True,
    min_size=(400, 300),
    background_color="#151515",
    frameless=True
)
window.events.closed += on_closed

api = JsonApi(window)
cmd_thread = threading.Thread(target=api.handle_commands, args=({self.port},), daemon=True)
cmd_thread.start()

webview.start()
'''
        self.process = subprocess.Popen([sys.executable, "-c", code])
        return self
    
    def send_command(self, cmd):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(("127.0.0.1", self.port))
            sock.send(json.dumps(cmd).encode())
            response = sock.recv(4096).decode()
            sock.close()
            return json.loads(response)
        except:
            return {"error": "Connection failed"}
    
    def navigate(self, url):
        return self.send_command({"action": "navigate", "url": url})
    
    def resize(self, width, height):
        return self.send_command({"action": "resize", "width": width, "height": height})
    
    def set_title(self, title):
        return self.send_command({"action": "set_title", "title": title})
    
    def fullscreen(self):
        return self.send_command({"action": "fullscreen"})
    
    def minimize(self):
        return self.send_command({"action": "minimize"})
    
    def get_url(self):
        return self.send_command({"action": "get_url"}).get("url", "")
    
    def close(self):
        return self.send_command({"action": "close"})


_browser = None

def execute_cmd(ars_window):
    global _browser
    
    browser_height = ars_window.prefs.code_editor_height if hasattr(ars_window.prefs, 'browser_height') else 600
    
    config = ContextMenuConfig()
    config.use_extended_shape = False
    config.auto_close = False
    config.close_on_outside = False
    config.distribution_mode = "x"
    config.custom_height = browser_height
    config.custom_width = ars_window.width()
    config.extra_distance = [0, 99999]

    # Start browser if not running
    if _browser is None or _browser.process.poll() is not None:
        _browser = BrowserController().start(
            url=DEFAULT_URL,
            width=ars_window.width(),
            height=browser_height - int(44 * 1.5)
        )

    options_list = [
        [
            "   ",
            ic.ICON_ARROW_BARS_V,
        ],
    ]

    config.slider_values = {
        ic.ICON_ARROW_BARS_V: (int(44 * 1.5), ars_window.height() - int(44 * 1.5) - 20, browser_height),
    }
    config.incremental_values = {
        ic.ICON_ARROW_BARS_V: (-20, "y"),
    }

    config.callbackL = {
        ic.ICON_ARROW_BARS_V: lambda value: (
            ctx.resize_top(value),
            _browser.resize(ars_window.width(), int(value) - int(44 * 1.5))
        ),
    }

    ctx = open_context(
        items=options_list,
        config=config
    )
    return ctx

