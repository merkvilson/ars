import numpy as np
from vispy import scene

from ars_3d_engine.mesh_objects.scene_objects import CGeometry
import pyvista as pv
from vispy.geometry import MeshData
from matplotlib import font_manager
import freetype
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.ops import unary_union
import mapbox_earcut as earcut


class CText3D(CGeometry):

    print("testing custom font import")


    def __init__(self, visual, name="Text3D", text="text", depth=0.5, angle=30.0, font_name="Dosis"):
        super().__init__(visual, name)
        self._text = text
        self._depth = depth
        self._angle = angle
        self._font_name = font_name

    @classmethod
    def create(cls, text="text", depth=0.5, color=(102/255, 108/255, 120/255, 1.0), translate=(0.0, 0.0, 0.0), name="Text3D", angle=30.0, font_name="Dosis"):
        md = CText3D._generate_mesh_data_with_breaking_angle(text, depth, angle, font_name)
        v = scene.visuals.Mesh(meshdata=md, color=color, shading=None)
        
        obj = cls(v, name=name, text=text, depth=depth, angle=angle, font_name=font_name)
        obj.set_position(*translate)
        return obj

    @staticmethod
    def _generate_mesh_data_with_breaking_angle(text, depth, angle, font_name="Dosis"):
        if not text or text.isspace():
            return MeshData()

        pv_mesh = None
        
        # Try custom font with freetype
        if font_name:
            try:
                # Find font file
                font_prop = font_manager.FontProperties(family=font_name)
                font_path = font_manager.findfont(font_prop)
                
                # Load font with freetype
                face = freetype.Face(font_path)
                face.set_char_size(48*2)  # default was 48*64
                
                # Collect all character outlines
                pen_x = 0
                all_char_polys = []  # List of polygons per character
                
                for char in text:
                    face.load_char(char, freetype.FT_LOAD_NO_BITMAP)
                    outline = face.glyph.outline
                    
                    if outline.n_points == 0:
                        pen_x += face.glyph.advance.x / 64.0
                        continue
                    
                    # Get contours from outline
                    points = np.array([(p[0]/64.0 + pen_x, p[1]/64.0) for p in outline.points])
                    
                    # Collect contours for this character
                    char_contours = []
                    start = 0
                    for end in outline.contours:
                        contour_points = points[start:end+1]
                        if len(contour_points) >= 3:
                            char_contours.append(contour_points)
                        start = end + 1
                    
                    # Build polygon with holes for this character
                    if char_contours:
                        # Determine which contours are holes based on containment
                        # The largest contour is usually the exterior
                        contours_with_area = []
                        for contour in char_contours:
                            try:
                                poly = ShapelyPolygon(contour)
                                if poly.is_valid:
                                    contours_with_area.append((poly.area, poly, contour))
                            except:
                                pass
                        
                        if contours_with_area:
                            # Sort by area (largest first)
                            contours_with_area.sort(key=lambda x: x[0], reverse=True)
                            
                            # The largest is the exterior
                            exterior_contour = contours_with_area[0][2]
                            exterior_poly = contours_with_area[0][1]
                            
                            # Check which other contours are inside (those are holes)
                            holes = []
                            for area, poly, contour in contours_with_area[1:]:
                                # If this contour is inside the exterior, it's a hole
                                if exterior_poly.contains(poly):
                                    holes.append(contour)
                            
                            # Create polygon with exterior and holes
                            try:
                                if holes:
                                    char_poly = ShapelyPolygon(exterior_contour, holes)
                                else:
                                    char_poly = ShapelyPolygon(exterior_contour)
                                
                                if char_poly.is_valid:
                                    all_char_polys.append(char_poly)
                            except:
                                pass
                    
                    pen_x += face.glyph.advance.x / 64.0
                
                if all_char_polys:
                    # Triangulate each polygon properly with earcut
                    all_verts = []
                    all_faces = []
                    
                    for poly in all_char_polys:
                        # Get exterior ring
                        exterior = np.array(poly.exterior.coords[:-1])
                        
                        # Get holes
                        holes = []
                        for interior in poly.interiors:
                            holes.append(np.array(interior.coords[:-1]))
                        
                        # Flatten all vertices
                        all_rings = [exterior] + holes
                        vertices_flat = np.vstack(all_rings)
                        
                        # Create ring end indices (cumulative count of vertices for each ring)
                        ring_ends = []
                        cumulative = 0
                        for ring in all_rings:
                            cumulative += len(ring)
                            ring_ends.append(cumulative)
                        
                        # Triangulate using earcut
                        triangles = earcut.triangulate_float64(vertices_flat, ring_ends)
                        
                        # Add to global arrays
                        vert_offset = len(all_verts)
                        all_verts.extend(vertices_flat)
                        
                        triangles_array = np.array(triangles).reshape(-1, 3)
                        all_faces.extend(triangles_array + vert_offset)
                    
                    if all_verts:
                        verts_array = np.array(all_verts)
                        verts_3d = np.c_[verts_array, np.zeros(len(verts_array))]
                        faces_array = np.array(all_faces, dtype=np.int32)
                        faces_pv = np.hstack([np.full((len(faces_array), 1), 3, dtype=np.int32), faces_array])
                        
                        mesh_2d = pv.PolyData(verts_3d, faces_pv)
                        pv_mesh = mesh_2d.extrude((0, 0, depth), capping=True)
                    
                if pv_mesh is None or pv_mesh.n_points == 0:
                    raise ValueError("Failed to generate mesh")
                    
            except Exception as e:
                print(f"Custom font '{font_name}' failed: {e}")
                raise  # Re-raise to prevent fallback

        # Compute normals
        pv_mesh.compute_normals(
            cell_normals=False,
            point_normals=True,
            split_vertices=True,
            feature_angle=angle,
            inplace=True,
        )

        # Extract data for VisPy
        vertices = pv_mesh.points.astype(np.float32)
        faces = pv_mesh.faces.reshape(-1, 4)[:, 1:].astype(np.uint32)
        normals = pv_mesh.point_normals.astype(np.float32)

        # Create final MeshData
        md = MeshData(vertices=vertices, faces=faces)
        if normals.shape[0] > 0:
            md._vertex_normals = normals
            
        return md

    def set_text(self, text: str) -> None:
        self._text = text
        md = CText3D._generate_mesh_data_with_breaking_angle(self._text, self._depth, self._angle, self._font_name)
        self._visual.set_data(meshdata=md)
        self._visual.update()

    def get_text(self) -> str:
        return self._text
