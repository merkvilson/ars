from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6 import QtCore
from vispy import scene
import numpy as np
from vispy.util.quaternion import Quaternion
from .grid.InfiniteGrid import InfiniteGrid
from .camera.ArsFlyCamera import ArsFlyCamera
from .bg import Background
from .logic.picking_manager import CPickingManager
from .logic.object_manager import CObjectManager
from vispy.scene import transforms
from .gizmo.gizmo import *
from scipy.spatial.transform import Rotation as ScipyRotation
from ars_cmds import bubble_cmds

class ViewportWidget(QWidget):
    def __init__(self, parent=None,):
        super().__init__(parent)
        self.setStyleSheet("border: none; background-color: black;")
        self._canvas = scene.SceneCanvas(keys=None, bgcolor=(39/255, 41/255, 45/255, 1), size=(100,100), show=False)
        #self.fps_counter = FPSCounter(self._canvas, self._canvas.native)

        self._view = self._canvas.central_widget.add_view()
        bounds = ((-150, 150), (0.5, 100), (-150, 150))
        cam = ArsFlyCamera(fov=60, up='+y', fly_bounds=bounds)
        self._view.camera = cam
        cam.update_callback = None
        cam.auto_roll = True
        cam.scale_factor = 10.0
        cam.center = (6, 3, 6)
        cam.rotation1 = Quaternion.create_from_axis_angle(np.deg2rad(-45), 0, 1, 0)
        cam.rotation2 = Quaternion.create_from_axis_angle(np.deg2rad(20), 1, 0, 0)
        cam.view_changed()
        self.cam = cam
        
        self._objectManager = CObjectManager(self._view, self._canvas, None, CPickingManager(self._canvas))

        # GIZMO SETUP
        gizmo_node = scene.Node(parent=self._view.scene)
        gizmo_node.order = 100  # Higher than default 0 for objects, so drawn last/on top
        gizmo_node.transform = transforms.MatrixTransform()

        self.gizmo_node = gizmo_node

        rot = Rotation()
        renderer = GizmoRenderer(parent_node=gizmo_node, base_thickness=0.06, segments=96, parent_view=self._view)
        controller = GizmoController(view=self._view, canvas=self._canvas, renderer=renderer, rotation=rot)

        self.controller = controller

        controller.set_handles(['t'])

        gizmo_node.visible = False


        def update_gizmo_visibility_and_position():
            selected = self._objectManager.get_selected_objects()
            if len(selected) == 1:
                obj = selected[0]
                pos = obj.get_position()

                # Sync controller's translation state with the selected object
                controller._object_translation = np.array(pos, dtype=float) 
                controller._ring_center = pos
                
                # --- ROBUSTLY SYNC ROTATION AND SCALE ---
                current_matrix = obj.rotation_visual.transform.matrix.copy()
                
                # Extract scale by getting the length of the basis vectors
                sx = np.linalg.norm(current_matrix[0,:3])
                sy = np.linalg.norm(current_matrix[1,:3])
                sz = np.linalg.norm(current_matrix[2,:3])
                
                # Handle potential zero-scale to avoid division by zero
                if sx < 1e-8: sx = 1e-8
                if sy < 1e-8: sy = 1e-8
                if sz < 1e-8: sz = 1e-8
                
                # Sync controller's scale state and update handle visuals
                controller.set_scale([sx, sy, sz])

                # Create a pure rotation matrix by removing the scale
                rot_matrix_part = current_matrix[:3, :3].copy()
                rot_matrix_part[0,:] /= sx
                rot_matrix_part[1,:] /= sy
                rot_matrix_part[2,:] /= sz
                
                # Sync controller's rotation state
                rot._rotation = ScipyRotation.from_matrix(rot_matrix_part)
                # --- END OF SYNC LOGIC ---

                # Move the gizmo node itself to the object's position
                tr = transforms.MatrixTransform()
                tr.translate(pos)
                gizmo_node.transform = tr
                
                gizmo_node.visible = True
                
                # Ensure handles are enabled (if they were disabled on hide)
                controller.set_handles(['t'])  # Or your default mode

            else:
                #gizmo_node.visible = False
               # controller.reset() 
                #controller._ring_center = np.array([0.0, 0.0, 0.0], dtype=float)  # Add this to reset hit centers
                controller.set_handles([])  # Add this to skip raycasts entirely when hidden


        self._objectManager.selection_changed.connect(update_gizmo_visibility_and_position)
        update_gizmo_visibility_and_position()

        def apply_gizmo_transforms():
            selected = self._objectManager.get_selected_objects()
            if len(selected) == 1:
                obj = selected[0]

                # --- APPLY TRANSFORMATION LOGIC ---
                
                # 1. Handle Translation on the parent node
                # This ensures translation happens independently of rotation and scale.
                T = transforms.MatrixTransform()
                T.translate(controller._object_translation)
                obj.visual.transform = T
                
                # The gizmo node itself also needs to follow the translation.
                gizmo_node.transform = T

                # 2. Handle Rotation and Scale on the child node
                # This combines the latest rotation and scale from the gizmo controller.
                
                # Get the latest rotation matrix from the gizmo
                R = rot.get_matrix()
                
                # Get the latest scale vector from the gizmo
                S_vec = controller._object_scale
                
                # Create a 4x4 scaling matrix
                S = np.eye(4, dtype=float)
                S[0,0] = S_vec[0]
                S[1,1] = S_vec[1]
                S[2,2] = S_vec[2]
                
                # Create the combined transformation matrix using the confirmed working order (S @ R).
                # This applies scale in the parent's coordinate space before rotation.
                transform_matrix = (S @ R).astype(np.float32)
                
                # Apply the combined matrix to the object's child visual (which handles rotation and scale).
                obj.rotation_visual.transform.matrix = transform_matrix
                
                # Request a canvas update to show the changes.
                self._canvas.update()

        controller.on_update = apply_gizmo_transforms

        @self._canvas.events.mouse_move.connect
        def on_mouse_move(event):
            # Let the controller update its internal state based on mouse movement
            controller.handle_mouse_move(event)

            # If the gizmo is not being dragged, just ensure the camera is interactive and do nothing else.
            if not controller._dragging:
                self._view.camera.interactive = True
                return

            # If dragging, disable camera interaction and get the selected object.
            self._view.camera.interactive = False
            apply_gizmo_transforms()


        @self._canvas.events.mouse_release.connect
        def on_mouse_release(event):
            # If a drag operation was in progress, commit the new scale
            # by updating the baseline scale for the next operation.
            if controller._dragging and controller._drag_mode == 'scale':
                controller.set_scale(controller._object_scale, reset_originals=True)
            
            controller.handle_mouse_release(event)
            self._view.camera.interactive = True

        @self._canvas.events.mouse_wheel.connect
        def on_mouse_wheel(event):
            controller.handle_mouse_wheel(event)

        ###########

        self.central_widget = self._canvas.central_widget
        self.bg = self.central_widget.add_widget(Background())

        self.grid_node = scene.Node(parent=self._view.scene)
        self.grid = InfiniteGrid(minor_step=1.0, subdivisions=10, visible_distance=100.0, 
                                  fade_exponent=0.4, show_y_axis=True, 
                                 y_axis_length=100.0)
        self.grid.parent = self.grid_node
        self.grid.set_y_axis_visible(False)
        cam.update_callback = self._update_grid

        self.attach_headlight(self._objectManager)


        layout = QVBoxLayout()
        layout.addWidget(self._canvas.native)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        self._canvas.native.setStyleSheet("border: none;")

        self._canvas.events.mouse_press.connect(self._on_mouse_press)
        self._canvas.native.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        #self.loc_r_gizmo_node = gizmo_node
        self.renderer = renderer
        self.controller = controller


    def attach_headlight(self, manager):
        initial_view_light_dir = (-150, -150, -150)
        initial_world_light_dir = self._view.camera.transform.imap(initial_view_light_dir)
        
        def update_lights():
            current_transform = self._view.camera.transform
            new_view_light_dir = current_transform.map(initial_world_light_dir)[:3]
            new_view_light_dir = new_view_light_dir / np.linalg.norm(new_view_light_dir)
            manager.update_lights(new_view_light_dir)
        
        if hasattr(self._view.camera, 'update_callback'):
            old_callback = self._view.camera.update_callback
            self._view.camera.update_callback = lambda: (old_callback() if old_callback else None, update_lights())
        else:
            @self._view.camera.transform.changed.connect
            def on_camera_transform_change(event):
                update_lights()


    def remove_object_at(self, index: int):
        obj = self._objectManager.remove_object_at(index)
        self._canvas.update()
        return obj

    def is_not_empty(self) -> bool:
        return self._objectManager.count() > 0

    # ===================================================================
    # MODIFIED SECTION
    # ===================================================================
    def _on_mouse_press(self, event):
        # Let the gizmo controller handle the event FIRST for any button.
        if hasattr(self, 'controller'):
            self.controller.handle_mouse_press(event)
            if event.handled:
                return  # If the gizmo was clicked, do nothing else.


        if event.button == 2:
            bubble_cmds.obj_att_mng(self.window())
            self.controller.set_handles([])


        # If the gizmo didn't handle it, proceed with object picking ONLY for left-clicks.
        if event.button != 1:
            return
            
        x, y = event.pos
        idx = self._objectManager.picking().pick_at(x, y)
        om = self._objectManager
        if idx is None:
            om.set_selection_state([], None)
            msg = "[_on_mouse_press] : object not found, selection cleared"
        else:
            cnt = om.count()
            if 0 <= idx < cnt:
                if QApplication.keyboardModifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                    indices = om.selected_indices()
                    if idx not in indices:
                        indices.append(idx)
                    om.set_selection_state(indices, om.active_index())
                    msg = f"[_on_mouse_press] : picked_index #{idx} (added to selection)"
                else:
                    om.set_selection_state([idx], idx)
                    msg = f"[_on_mouse_press] : picked_index #{idx}"
            else:
                raise RuntimeError(f"Pick returned invalid index {idx}, len(objects)={cnt}")
                    
        self._canvas.update()

        selected = om.get_selected_objects()
        if selected:
            positions = [obj.get_position() for obj in selected]
            center = np.mean(positions, axis=0)
        self._canvas.update()


    def _update_grid(self):
        cam_pos = self._view.camera.center
        self.grid.update_grid(cam_pos)