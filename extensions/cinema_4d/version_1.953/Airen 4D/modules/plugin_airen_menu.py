import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *

from c4d_gui_cmd import *


class C_AI_AIREN_4D_MENU(c4d.plugins.CommandData):
    def Execute(self, doc):


        def check_r(value):
            if value: return "&c&"
            else: return ""


        bc = c4d.BaseContainer()

        cmd_bc = c4d.BaseContainer()
        cmd_bc.InsData(1, 'Commands')
        cmd_bc.InsData(1062009, "CMD") #Render View
        bc.SetContainer(0, cmd_bc)  # Set sub menu as sub container

        mod_bc = c4d.BaseContainer()
        mod_bc.InsData(1, 'Modifiers')
        for mod_id in mods_ids: mod_bc.InsData(mod_id, "CMD")
        bc.SetContainer(2, mod_bc)  # Set sub menu as sub container

        gen_bc = c4d.BaseContainer()
        gen_bc.InsData(1, 'Generators')
        for env_id in envs_ids:gen_bc.InsData(env_id, "CMD") #Stage       

        
        gen_bc.InsData(0, '')       
        gen_bc.InsData(1062684, "CMD") #Terrain
        gen_bc.InsData(AI_3D, "CMD") #Terrain
        gen_bc.InsData(AI_SPRITE, "CMD") #Sprite
        bc.SetContainer(3, gen_bc)  # Set sub menu as sub container


        tag_bc = c4d.BaseContainer()
        tag_bc.InsData(1, 'Tags')
        tag_bc.InsData(1062699, "CMD") #Interaction Tag
        bc.SetContainer(4, tag_bc)  # Set sub menu as sub container


        key_bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):
            result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )
            
            #c4d.CallCommand(result)


        return True
