import numpy as np
from vispy import app, scene
from vispy.visuals import mesh
from shapely.text import Text
from shapely.affinity import scale
from mapbox_earcut import triangulate_float64


def create_3d_text(text, depth=0.2, font_size=1.0):
    """Generate extruded 3D text geometry (verts, faces)"""
    # Convert text to 2D polygons using Shapely
    shape = Text(text, size=font_size).buffer(0)
    shape = scale(shape, xfact=1, yfact=-1, origin=(0, 0))  # flip Y

    verts_all = []
    faces_all = []

    def add_polygon(polygon, z_offset):
        """Triangulate polygon and append vertices/faces"""
        exterior = np.array(polygon.exterior.coords, dtype=np.float64).flatten()
        holes = []
        hole_index = len(polygon.exterior.coords)

        for interior in polygon.interiors:
            holes.append(hole_index)
            hole_index += len(interior.coords)
            exterior = np.concatenate([exterior, np.array(interior.coords, dtype=np.float64).flatten()])

        # convert to numpy arrays for earcut
        verts_2d = np.array(exterior, dtype=np.float64)
        holes_arr = np.array(holes, dtype=np.uint32)
        tris = np.array(triangulate_float64(verts_2d, holes_arr)).reshape(-1, 3)

        verts_2d = verts_2d.reshape(-1, 2)
        verts_3d = np.column_stack([verts_2d, np.full(len(verts_2d), z_offset)])

        faces_all.append(tris + len(verts_all))
        verts_all.append(verts_3d)

    # Handle single or multiple polygons
    if shape.geom_type == "Polygon":
        add_polygon(shape, 0)
        add_polygon(shape, depth)
    elif shape.geom_type == "MultiPolygon":
        for poly in shape.geoms:
            add_polygon(poly, 0)
            add_polygon(poly, depth)

    verts = np.vstack(verts_all)
    faces = np.vstack(faces_all)

    # Connect side walls
    side_faces = []
    count = len(verts) // 2
    for i in range(count - 1):
        a, b = i, i + 1
        c, d = a + count, b + count
        side_faces.append([a, b, d])
        side_faces.append([a, d, c])

    faces = np.vstack([faces, np.array(side_faces, dtype=np.uint32)])
    return verts, faces


# Create scene
canvas = scene.SceneCanvas(keys='interactive', bgcolor='black', show=True)
view = canvas.central_widget.add_view()
view.camera = 'turntable'

# Generate 3D text mesh
verts, faces = create_3d_text("VISPY", depth=0.3, font_size=1.5)

# Add mesh visual
mesh = scene.visuals.Mesh(vertices=verts, faces=faces, color=(0.3, 0.8, 1, 1), shading='smooth')
view.add(mesh)

# Run
if __name__ == '__main__':
    app.run()
