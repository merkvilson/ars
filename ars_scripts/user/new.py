cube = add_primitive("cube")

sphere = add_primitive("sphere")
sphere.set_position(3,0,3)

torus = add_primitive("torus")
torus.set_position(-3,0,3)

plane = add_primitive("plane")
plane.set_position(3,0,-3)

sphere.pick()

# obj = get_selected()
# obj.set_color((0,1,0))
