import numpy as np
from vispy import app, scene
from vispy.color import Color
from vispy.visuals.transforms import MatrixTransform
from core.sound_manager import play_sound

def _create_cube_mesh(size=1.0, color='white', alpha=1.0, parent=None):
    """Create a cube using Mesh visual with proper backface culling support"""
    
    # Define cube vertices (8 corners)
    vertices = np.array([
        [-size/2, -size/2, -size/2],
        [size/2, -size/2, -size/2],
        [size/2, size/2, -size/2],
        [-size/2, size/2, -size/2],
        [-size/2, -size/2, size/2],
        [size/2, -size/2, size/2],
        [size/2, size/2, size/2],
        [-size/2, size/2, size/2],
    ], dtype=np.float32)
    
    # Define cube faces (12 triangles)
    faces = np.array([
        # Front face (z+)
        [4, 6, 5], [4, 7, 6],
        # Back face (z-)
        [1, 3, 0], [1, 2, 3],
        # Right face (x+)
        [5, 2, 1], [5, 6, 2],
        # Left face (x-)
        [0, 7, 4], [0, 3, 7],
        # Top face (y+)
        [7, 2, 6], [7, 3, 2],
        # Bottom face (y-)
        [0, 5, 1], [0, 4, 5],
    ], dtype=np.uint32)
    
    # Create mesh
    if isinstance(color, str):
        col = Color(color, alpha=alpha)
    else:
        col = Color(color + (alpha,))
    mesh = scene.visuals.Mesh(
        vertices=vertices,
        faces=faces,
        color=col,
        shading=None,
        parent=parent
    )
    
    # Enable backface culling
    mesh.set_gl_state(
        depth_test=True,
        cull_face='back',
        blend=True,
        blend_func=('src_alpha', 'one_minus_src_alpha')
    )
    
    return mesh


def _create_plane_mesh(width=1.0, height=1.0, color='white', alpha=1.0, parent=None):
    """Create an XY-oriented plane (facing +Z) using a Mesh visual."""
    half_w = width / 2.0
    half_h = height / 2.0
    vertices = np.array([
        [-half_w, -half_h, 0.0],
        [ half_w, -half_h, 0.0],
        [ half_w,  half_h, 0.0],
        [-half_w,  half_h, 0.0],
    ], dtype=np.float32)

    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
        ],
        dtype=np.uint32,
    )

    if isinstance(color, str):
        col = Color(color, alpha=alpha)
    else:
        col = Color(color + (alpha,))

    mesh = scene.visuals.Mesh(
        vertices=vertices,
        faces=faces,
        color=col,
        shading=None,
        parent=parent,
    )

    mesh.set_gl_state(
        depth_test=True,
        cull_face='back',
        blend=True,
        blend_func=('src_alpha', 'one_minus_src_alpha'),
    )

    return mesh

def bbox_loading_animation(parent, bbox_scale=4.0, count=3):
    play_sound("bbox-in")
    # Create 27 mini-cubes in a 3x3x3 grid
    mini_cube_size = (bbox_scale / count)
    spacing = mini_cube_size
    grid_points = np.linspace(-spacing, spacing, count)  # 3 points along each axis
    positions = [(x, y, z) for x in grid_points for y in grid_points for z in grid_points]
    
    # Animation parameters
    min_scale = 0.01
    max_scale = (bbox_scale / count) * (1/count)
    animation_period = 2.0  # Duration of one full scale cycle in seconds
    fade_in_duration = 0.5  # Duration to fade in the main cube alpha
    initial_scale = 0.0001  # Extremely small to hide initial flash
    scale_up_duration = 0.1  # Quick scale-up for big cube
    
    # Create mini-cubes and store their transforms
    cubes = []
    transforms = []
    phase_offsets = np.random.uniform(0, 2 * np.pi, len(positions))  # Random phase for each cube
    start_delays = np.random.uniform(0, 0.5, len(positions))  # Random start delays
    removal_delays = np.random.uniform(0, 0.5, len(positions))  # Random removal delays
    
    # State tracking
    removing = [False]
    removal_start_time = [None]
    animation_start_time = [None]
    
    for i, pos in enumerate(positions):
        box = _create_cube_mesh(size=mini_cube_size, color=(0.9, 0.9, 0.9), alpha=1.0, parent=None)
        transform = MatrixTransform()
        transform.scale([initial_scale, initial_scale, initial_scale])  # Start tiny
        transform.translate(pos)
        box.transform = transform
        box.update()
        box.parent = parent  # Add after setup
        cubes.append(box)
        transforms.append(transform)
    
    # Create a semi-transparent cube with initial alpha=0 and tiny scale
    cube = _create_cube_mesh(size=bbox_scale, color=(1.0, 1.0, 1.0), alpha=0.0, parent=None)
    transform_big = MatrixTransform()
    transform_big.scale([initial_scale, initial_scale, initial_scale])  # Start tiny
    cube.transform = transform_big
    cube.update()
    cube.parent = parent  # Add after setup
    parent.canvas.update()  # Force sync
    
    # Animation loop
    def update(event):
        time = event.elapsed  # Time since application start
        
        # Track animation start time
        if animation_start_time[0] is None:
            animation_start_time[0] = time
        
        elapsed = time - animation_start_time[0]
        
        # If removing, handle removal animation
        if removing[0]:
            if removal_start_time[0] is None:
                removal_start_time[0] = time
            
            elapsed_removal = time - removal_start_time[0]
            all_done = True
            
            for i, (cube_obj, transform) in enumerate(zip(cubes, transforms)):
                time_since_removal = elapsed_removal - removal_delays[i]
                
                if time_since_removal < 0:
                    # Not yet started removing
                    all_done = False
                    continue
                elif time_since_removal < 0.3:
                    # Scale down over 0.3 seconds
                    all_done = False
                    progress = time_since_removal / 0.3
                    scale = 0.5 * (1.0 - progress)
                    scale = max(initial_scale, scale)
                else:
                    # Fully removed
                    scale = initial_scale
                
                transform.matrix = np.eye(4)
                transform.scale([scale, scale, scale])
                transform.translate(positions[i])
                cube_obj.update()
            
            # Fade out main cube alpha over 0.5 seconds
            if elapsed_removal < fade_in_duration:
                progress = elapsed_removal / fade_in_duration
                alpha = 0.2 * (1.0 - progress)
            else:
                alpha = 0.0
            
            cube.color = Color((1.0, 1.0, 1.0), alpha=alpha)
            cube.update()
            
            # If all done, cleanup
            if all_done and elapsed_removal >= fade_in_duration:
                timer.stop()
                for cube_obj in cubes:
                    cube_obj.parent = None
                cube.parent = None
                
        else:
            # Normal animation
            for i, (cube_obj, transform) in enumerate(zip(cubes, transforms)):
                adjusted_time = elapsed - start_delays[i]
                
                if adjusted_time < 0:
                    # Not yet started
                    scale = initial_scale
                elif adjusted_time < 0.3:
                    # Scale up from initial_scale to target over 0.3 seconds
                    progress = adjusted_time / 0.3
                    target_scale = min_scale + (max_scale - min_scale) * (0.5 + 0.5 * np.sin(2 * np.pi * adjusted_time / animation_period + phase_offsets[i]))
                    scale = initial_scale + (target_scale - initial_scale) * progress
                else:
                    # Normal animation
                    scale = min_scale + (max_scale - min_scale) * (0.5 + 0.5 * np.sin(2 * np.pi * adjusted_time / animation_period + phase_offsets[i]))
                
                # Reset transform to identity
                transform.matrix = np.eye(4)
                # Apply scaling
                transform.scale([scale, scale, scale])
                # Re-apply translation
                transform.translate(positions[i])
                cube_obj.update()
            
            # Quick scale-up for big cube over 0.1 seconds
            if elapsed < scale_up_duration:
                scale_progress = elapsed / scale_up_duration
                big_scale = initial_scale + (1.0 - initial_scale) * scale_progress
            else:
                big_scale = 1.0
            
            transform_big.matrix = np.eye(4)
            transform_big.scale([big_scale, big_scale, big_scale])
            
            # Fade in main cube alpha over 0.5 seconds
            if elapsed < fade_in_duration:
                progress = elapsed / fade_in_duration
                alpha = 0.1 * progress
            else:
                alpha = 0.1
            
            cube.color = Color((1.0, 1.0, 1.0), alpha=alpha)
            cube.update()
    
    # Create a timer to drive the animation
    timer = app.Timer(interval=1/60, connect=update, start=True)
    
    # Attach cleanup data to the timer itself
    timer._animation_cubes = cubes
    timer._animation_main_cube = cube
    timer._removing = removing
    timer._transform_big = transform_big
    
    # Track on parent for global deletion
    if not hasattr(parent, '_animation_meshes'):
        parent._animation_meshes = []
    if not hasattr(parent, '_animation_timers'):
        parent._animation_timers = []
    parent._animation_meshes.extend(cubes + [cube])
    parent._animation_timers.append(timer)
    
    return timer

def remove_bbox_loading_animation(timer):
    play_sound("bbox-out")
    # Just set the flag to start removal animation
    timer._removing[0] = True


def plane_fill_animation(parent, plane_scale=4.0, count=4, grow_duration=0.3):
    """Create a 2D grid of planes that scale in once to form a single larger plane."""

    plane_size = plane_scale / count
    indices = np.linspace(-(count - 1) / 2.0, (count - 1) / 2.0, count)
    positions = [(ix * plane_size, iy * plane_size, 0.0) for iy in indices for ix in indices]
    positions = [positions[i] for i in np.random.permutation(len(positions))]

    initial_scale = 0.0001
    start_delays = np.linspace(0.0, 0.4, len(positions))

    planes = []
    transforms = []

    for pos in positions:
        plane = _create_plane_mesh(width=plane_size, height=plane_size, color=(0.5, 0.5, 0.5), alpha=1.0, parent=None)
        transform = MatrixTransform()
        transform.scale([initial_scale, initial_scale, 1.0])
        transform.translate(pos)
        plane.transform = transform
        plane.update()
        plane.parent = parent
        planes.append(plane)
        transforms.append(transform)

    parent.canvas.update()

    def update(event):
        elapsed = event.elapsed
        all_finished = True

        for idx, (plane, transform) in enumerate(zip(planes, transforms)):
            delay = start_delays[idx]
            local_time = elapsed - delay

            if local_time <= 0:
                scale_factor = initial_scale
                all_finished = False
            elif local_time < grow_duration:
                progress = local_time / grow_duration
                scale_factor = initial_scale + (1.0 - initial_scale) * progress
                all_finished = False
            else:
                scale_factor = 1.0

            transform.matrix = np.eye(4)
            transform.scale([scale_factor, scale_factor, 1.0])
            transform.translate(positions[idx])
            plane.update()

        if all_finished:
            timer.stop()
            for plane in planes:
                plane.parent = None

    timer = app.Timer(interval=1 / 60, connect=update, start=True)
    timer._animation_planes = planes

    # Track on parent for global deletion
    if not hasattr(parent, '_animation_meshes'):
        parent._animation_meshes = []
    if not hasattr(parent, '_animation_timers'):
        parent._animation_timers = []
    parent._animation_meshes.extend(planes)
    parent._animation_timers.append(timer)
    
    return timer

def delete_bbox_animations(parent):
    if hasattr(parent, '_animation_timers'):
        for t in parent._animation_timers:
            t.stop()
        parent._animation_timers = []
    if hasattr(parent, '_animation_meshes'):
        for m in parent._animation_meshes:
            m.parent = None
        parent._animation_meshes = []