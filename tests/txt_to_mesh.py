import pyvista as pv

# Define the text to convert to 3D mesh
text = "Hello 3D"

# Create the 3D text mesh with a specified depth for extrusion
mesh = pv.Text3D(text, depth=0.5)

# Save the mesh to a file (e.g., STL format for 3D printing or further use)
mesh.save("3d_text.stl")
