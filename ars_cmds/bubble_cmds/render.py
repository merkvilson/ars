from PyQt6.QtCore import QTimer, QUrl, QFileSystemWatcher
from PyQt6.QtWebSockets import QWebSocket
from PyQt6.QtNetwork import QAbstractSocket
from PyQt6.QtGui import QCursor

from ui.widgets.context_menu import ContextMenuConfig, open_context
from theme.fonts import font_icons as ic

from ars_cmds.render_cmds.make_screenshot import make_screenshot
from ars_cmds.render_cmds.render_pass import save_depth, save_render
from ars_cmds.render_cmds.check import check_queue
from ars_cmds.core_cmds.key_check import key_check
from ars_cmds.util_cmds.copy_to import copy_file_to_dir
from ars_cmds.mesh_gen.generate_mesh import generate_mesh

from prefs.pref_controller import get_path

import os
import uuid
import json

from PyQt6.QtGui import QColor

def BBL_RENDER(self, position, workflow = None):
    
    workflow = workflow if workflow else self.render_manager.workflow_name


    config = ContextMenuConfig()
    config.auto_close = False
    config.distribution_mode = 'x'
    config.use_extended_shape = False
    config.use_extended_shape_items = {ic.ICON_IMAGE: True}
    config.color = {ic.ICON_IMAGE: QColor(0, 0, 0,0)}

    options_list = [ [ic.ICON_IMAGE], [ ic.ICON_STEPS, ic.ICON_GIZMO_SCALE,"   ", ic.ICON_RENDER, "   ", ic.ICON_SAVE, "x",]]
    config.per_item_radius = {
        ic.ICON_IMAGE: 45,}
    config.image_items = {ic.ICON_IMAGE: r" "}

    config.additional_texts = {
        ic.ICON_RENDER: "Start Render",
        ic.ICON_STEPS: "Steps",
        ic.ICON_SAVE: "Save"
    }

    config.slider_values = {
        ic.ICON_STEPS: (1, 50, self.render_manager.get_userdata("steps")),
        ic.ICON_GIZMO_SCALE: (25, 1024, 512),
    }

    config.show_value_items = {
        ic.ICON_STEPS: True,
        ic.ICON_RENDER: True,
        ic.ICON_GIZMO_SCALE: True,
    }

    # Initialize WebSocket
    client_id = str(uuid.uuid4())
    ws_uri = f"ws://127.0.0.1:8188/ws?clientId={client_id}"
    ws = QWebSocket()
    reconnect_timer = QTimer()
    reconnect_timer.setSingleShot(True)
    

    def start_reconnect():
        if not reconnect_timer.isActive():
            reconnect_timer.start(3000)
 
    def on_connected():
        print("WebSocket connected")

    def on_disconnected():
        print("WebSocket disconnected")
        start_reconnect()

    def on_error(error):
        print(f"WebSocket error: {error}")
        start_reconnect()

    def connect_websocket():
        if ws.state() != QAbstractSocket.SocketState.ConnectedState:
            print("Attempting WebSocket connection")
            ws.open(QUrl(ws_uri))

    ws.connected.connect(on_connected)
    ws.disconnected.connect(on_disconnected)
    ws.errorOccurred.connect(on_error)
    reconnect_timer.timeout.connect(connect_websocket)

    weights =self.render_manager.get_weights()
    
    for weight_item, weight_value in weights.items():
        print(f"Weight Item: {weight_item}, Weight Value: {weight_value}")


    def on_text_message(message):
        data = json.loads(message)
        msg_type = data.get("type")
        if msg_type == "progress":
            # Handle progress messages for KSampler
            node_id = data.get("data", {}).get("node")
            value = data.get("data", {}).get("value", 0)
            max_val = max(data.get("data", {}).get("max", 1), 1)
            
            for weight_item, weight_value in weights.items():
                if node_id == weight_item:
                    percent = int((value / max_val) * 100)
                    print(f"KSampler progress: node_id={node_id}, value={value}, max={max_val}, percent={percent}")
                    ctx.update_item(ic.ICON_RENDER, "progress", percent)
                    ctx.update_item(ic.ICON_RENDER, "additional_text", f"Rendering... {percent}%")
                    if percent == 100:
                        check_queue(revert_to_normal)


        elif msg_type == "status":
            exec_info = data.get("data", {}).get("status", {}).get("exec_info", {})
            queue_remaining = exec_info.get("queue_remaining", 1)
            print(f"Queue status: {queue_remaining} remaining")
            if queue_remaining == 0:
                revert_to_normal()
        update_image()

    self._render_timer = None

    def start_polling():
        if self._render_timer and self._render_timer.isActive():
            return
        self._render_timer = QTimer(self)
        self._render_timer.timeout.connect(update_image)
        self._render_timer.start(500)

    def stop_polling():
        if self._render_timer:
            self._render_timer.stop()

    def update_image():
        if self.viewport.isVisible():
            ctx.update_item(ic.ICON_IMAGE, "image_path", get_path('last_step'))
        if not self.viewport.isVisible() and hasattr(self, 'img') and self.img and get_path('last_step'):
            self.img.open_image(get_path('last_step'))

    def swap_imge(self):
        image_path = os.path.join(get_path('input'), "vp_screenshot.png")
        if self.viewport.isVisible():
            def post_screenshot():
                ctx.update_item(ic.ICON_IMAGE, "image_path", image_path)
                files = os.listdir(get_path('steps')) 
                full_paths = [os.path.join(get_path('steps'), f) for f in files]
                if full_paths:
                    latest_file = max(full_paths, key=os.path.getmtime)
                    if hasattr(self, 'img') and self.img:
                        self.img.open_image(latest_file)
                self.swap_widgets()
            
            make_screenshot(self, callback=post_screenshot, x=200, y=200, name="vp_screenshot.png")
        else:
            self.swap_widgets()
            update_image()

    def revert_to_normal():
        ctx.update_item(ic.ICON_RENDER, "progress_bar", 0)
        ctx.update_item(ic.ICON_RENDER, "additional_text", "Start Render")
        stop_polling()
        print("Render complete")
        if queue_timer.isActive():
            queue_timer.stop()

    queue_timer = QTimer()
    queue_timer.timeout.connect(lambda: check_queue(revert_to_normal))


    def save_output(name = self.render_manager.workflow_name):
        if name == "mesh_image":
            copy_file_to_dir(get_path('last_step'), get_path('input'), "mesh", False)
        elif name == "render":
            copy_file_to_dir(get_path('last_step'), get_path('keyframes'), "frame", True)



    def start_render():
        if workflow in ("render", "mesh_image"):
            ctx.update_item(ic.ICON_RENDER, "progress_bar", 1)
            ctx.update_item(ic.ICON_RENDER, "progress", 0)
            ctx.update_item(ic.ICON_RENDER, "additional_text", "Rendering... 0%")
            self.render_manager.set_userdata("seed", self.render_manager.get_userdata("seed") + 1 if key_check("shift") else -1 if key_check("ctrl") else 0)
            connect_websocket()
            save_depth(self.viewport, x=int(ctx.get_value(ic.ICON_GIZMO_SCALE)), y=int(ctx.get_value(ic.ICON_GIZMO_SCALE)))
            save_render(self.viewport, x=int(ctx.get_value(ic.ICON_GIZMO_SCALE)), y=int(ctx.get_value(ic.ICON_GIZMO_SCALE)))
            self.render_manager.send_render()
            start_polling()
            queue_timer.start(500)
        elif workflow == "mesh":
            generate_mesh(self, ctx)

    config.callbackL = {
        ic.ICON_RENDER: lambda: start_render(),
        ic.ICON_STEPS: lambda value: self.render_manager.set_userdata("steps", value),
        ic.ICON_GIZMO_SCALE: lambda value: print(value),
        ic.ICON_SAVE: lambda: save_output(),
        ic.ICON_IMAGE: lambda: (swap_imge(self), self.img.fit_image()),

    }

    ctx = open_context(
        parent=self.central_widget,
        items=options_list,
        position=position,
        config=config
    )

    ws.textMessageReceived.connect(on_text_message)
    connect_websocket()

    ctx.destroyed.connect(stop_polling)
    ctx.destroyed.connect(ws.close)
    ctx.destroyed.connect(reconnect_timer.stop)
    ctx.destroyed.connect(queue_timer.stop)