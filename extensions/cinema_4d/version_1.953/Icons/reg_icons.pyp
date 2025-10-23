import c4d
import os

plugin_dir = os.path.split(__file__)[0]
large =os.path.join(plugin_dir, "large")
small =os.path.join(plugin_dir, "small")
mods  =os.path.join(plugin_dir, "mods")



def reg_icon(id, file, name):
    image = c4d.bitmaps.BaseBitmap()
    fn = os.path.join(file, name)
    image.InitWith(fn)
    c4d.gui.RegisterIcon(id, image)


for icon in os.listdir(large):
    icon_id = int(icon.split(".")[0])
    reg_icon(icon_id, large, icon)

for icon in os.listdir(small):
    icon_id = int(icon.split(".")[0])
    reg_icon(icon_id, small, icon)

for icon in os.listdir(mods):
    icon_id = int(icon.split(".")[0])
    reg_icon(icon_id, mods, icon)
