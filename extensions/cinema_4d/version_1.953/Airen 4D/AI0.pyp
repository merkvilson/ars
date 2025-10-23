#TODO: Mesh To Texture > insert 3d object and using canny controlnet, generate new texture for it.

import os 

import base64 as b, types as t, zlib as z; m=t.ModuleType('localimport');
with open(os.path.join(os.path.split(__file__)[0], "modules","localimport"), 'r') as file: content = file.read()
m.__file__ = __file__; blob=content
exec(z.decompress(b.b64decode(blob)), vars(m)); _localimport=m;localimport=getattr(m,"localimport")
del blob, b, t, z, m;

with localimport('modules'): 
    from generate    import *
    from airen_paths import *
    from airen_nodes import *
    from c4d_gui     import *
    from c4d_gui_fr  import *
    from plugin_ids  import *
    from airen_cmds  import *
    from airen_vars  import *
    from c4d_gui_cmd import *

    from plugin_shader       import *
    from plugin_bg           import *
    from plugin_stage_prompt import *
    from plugin_p_prompt     import *
    from plugin_render_view  import *
    from plugin_terrain      import *
    from plugin_sprite       import *
    from plugin_mesh         import *
    from plugin_inter_tag    import *
    from plugin_airen_menu   import *


import c4d
from   c4d.utils import Rad as r

import random
import subprocess

import time
import ast

import json
import base64
import winreg
import re
import shutil






class Oaisky(OSceneBG): 
    pass


class Oaibg(OSceneBG): 
    pass


class C_Par_RndPick(c4d.plugins.CommandData):
    def Execute(self, doc):
        apply_parametric_settings('Random Picker', 2, 0.0, '1063056')
        c4d.EventAdd()
        return True


class C_Par_LOD    (c4d.plugins.CommandData):
    def Execute(self, doc):
        apply_parametric_settings('Level Of Details', 1, 0.0, '1063052')
        return True


class C_Par_Prompt (c4d.plugins.CommandData):
    def Execute(self, doc):
        apply_parametric_settings('Parametric Prompt', 0, 0.0, '1063055')
        return True



class C_Par_Morph (c4d.plugins.CommandData):
    def Execute(self, doc):
        apply_parametric_settings('Prompt Morph', 3, 0.0, '1063054')
        return True



class C_Par_Time    (c4d.plugins.CommandData):
    def Execute(self, doc):

        c4d.gui.MessageDialog(f"This option will be available in the next update")
        #apply_parametric_settings('Time', 4, 0.0, 'time')
        #c4d.EventAdd()
        return True



class C_Par_Season  (c4d.plugins.CommandData):
    def Execute(self, doc):
        c4d.gui.MessageDialog(f"This option will be available in the next update")

        #c4d.CallCommand(AI_PARAMETRIC_P)
        #apply_parametric_settings('Season', 5, 0.0, 'season')
        #c4d.EventAdd()
        return True



class C_Par_LORA  (c4d.plugins.CommandData):
    def Execute(self, doc):
        apply_parametric_settings('Lora', 6, 1.0, '1063053')
        return True



class C_DIR_BG (c4d.plugins.CommandData):
    def Execute(self, doc):
        subprocess.Popen(['explorer', sd_bg_dir])
        return True

class C_DIR_DOME (c4d.plugins.CommandData):
    def Execute(self, doc):
        subprocess.Popen(['explorer', sd_dome_dir])
        return True

class C_DIR_TEX (c4d.plugins.CommandData):
    def Execute(self, doc):
        subprocess.Popen(['explorer', sd_tex_dir])
        return True

class C_DIR_TERRAIN (c4d.plugins.CommandData):
    def Execute(self, doc):
        subprocess.Popen(['explorer', sd_terrain_dir])
        return True

class C_DIR_SPRITE (c4d.plugins.CommandData):
    def Execute(self, doc):
        subprocess.Popen(['explorer', sd_sprite_dir])
        return True

class C_DIR_RENDERS (c4d.plugins.CommandData):
    def Execute(self, doc):
        subprocess.Popen(['explorer', sd_saved_render])
        return True



class Airen_Material(c4d.plugins.CommandData):

    dialog = None

    def Execute(self, doc):
        print("Material Is Coming Soon")
        return




if __name__ == "__main__":

    base_dir = os.path.split(__file__)[0]
    def ico(name):
        bmp = c4d.bitmaps.BaseBitmap()  
        bmp.InitWith(os.path.join(base_dir, "res", "icons", f"{name}.png") )
        return bmp

    c4d.plugins.RegisterShaderPlugin    (id =  AI_TEXTURE   ,str = "Airen Texture" ,g =  AI0 ,description  = "AI0" ,info =  0 ,)
    
    c4d.plugins.RegisterTagPlugin       (id= AI_INTER_TAG, str= "Airen Interaction",info= c4d.TAG_VISIBLE | c4d.TAG_EXPRESSION | c4d.TAG_MULTIPLE,g= Tbg_inter,description= "Tbg_inter", icon= ico("interaction"))

    c4d.plugins.RegisterObjectPlugin    (id = AI_SCENE_PROMPT,str = "Stage Prompt",g = Ostage_prompt, description = "Oscene_prompt", info = c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,icon = ico("stage"))
    c4d.plugins.RegisterObjectPlugin    (id = AI_PARAMETRIC_P,str = "PROMPT_EFFECTOR_0",g = Opprompt, description = "Opprompt", info = c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,icon = ico("parametric"))
    c4d.plugins.RegisterObjectPlugin    (id = AI_SKY,str = "Dome",g = Oaisky, description = "Oaisky", info = c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,icon = ico("sky"))
    c4d.plugins.RegisterObjectPlugin    (id = AI_BG,str = "Background",g = Oaibg, description = "Oaibg", info = c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,icon = ico("bg"))
    c4d.plugins.RegisterObjectPlugin    (id = AI_TERRAIN_GEN,str = "Terrain",g = OAi_Terrain, description = "", info = c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,icon = ico("height_gen"))
    c4d.plugins.RegisterObjectPlugin    (id = AI_3D,str = "3D Mesh",g = OAI_3D, description = "", info = c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,icon = ico("obj3d"))
    c4d.plugins.RegisterObjectPlugin    (id = AI_SPRITE,str = "Sprite",g = OAI_SPRITE, description = "", info = c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,icon = ico("sprite"))

    c4d.plugins.RegisterCommandPlugin (AI_RENDER_WINDOW,"Airen Render View",134217728 | 268435456 ,ico("render"), "", Airen_Window())
    c4d.plugins.RegisterCommandPlugin (id = AI_MATERIAL,  str = "Airen Material",info   = c4d.PLUGINFLAG_COMMAND_HOTKEY|c4d.PLUGINFLAG_HIDEPLUGINMENU,dat = Airen_Material(),help   = "Airen Material",icon   = ico("folder"))
    c4d.plugins.RegisterCommandPlugin (id= AI_INTER_TAG_CMD, str= "Interaction Tag",info= c4d.PLUGINFLAG_COMMAND_HOTKEY|c4d.PLUGINFLAG_HIDEPLUGINMENU,dat= Cbg_inter(),help= "Create Tag",icon= ico("interaction") )

    c4d.plugins.RegisterCommandPlugin (AI_C_Par_RndPick , "Random Picker"      , 134217728 | 268435456 , ico("rnd")   , "", C_Par_RndPick())
    c4d.plugins.RegisterCommandPlugin (AI_C_Par_LOD     , "Level Of Details"   , 134217728 | 268435456 , ico("lod3")  , "", C_Par_LOD    ())
    c4d.plugins.RegisterCommandPlugin (AI_C_Par_Prompt  , "Parametric Prompt"  , 134217728 | 268435456 , ico("par")   , "", C_Par_Prompt ())
    c4d.plugins.RegisterCommandPlugin (AI_C_Par_Morph   , "Prompt Morph"       , 134217728 | 268435456 , ico("morph") , "", C_Par_Morph ())
    c4d.plugins.RegisterCommandPlugin (AI_C_Par_Time    , "Time"               , 134217728 | 268435456 , ico("time")  , "", C_Par_Time ())
    c4d.plugins.RegisterCommandPlugin (AI_C_Par_Season  , "Season"             , 134217728 | 268435456 , ico("season"), "", C_Par_Season ())
    c4d.plugins.RegisterCommandPlugin (AI_C_Par_LORA    , "Lora"               , 134217728 | 268435456 , ico("lora")  , "", C_Par_LORA ())

    c4d.plugins.RegisterCommandPlugin (AI_C_DIR_BG      , "Background"         , 134217728 | 268435456 , ico("folder") , "",        C_DIR_BG ())
    c4d.plugins.RegisterCommandPlugin (AI_C_DIR_DOME    , "Dome"               , 134217728 | 268435456 , ico("folder") , "",      C_DIR_DOME ())
    c4d.plugins.RegisterCommandPlugin (AI_C_DIR_TEX     , "Textures"           , 134217728 | 268435456 , ico("folder") , "",       C_DIR_TEX ())
    c4d.plugins.RegisterCommandPlugin (AI_C_DIR_TERRAIN , "Terrain"            , 134217728 | 268435456 , ico("folder") , "",   C_DIR_TERRAIN ())
    c4d.plugins.RegisterCommandPlugin (AI_C_DIR_SPRITE  , "Sprite"             , 134217728 | 268435456 , ico("folder") , "",    C_DIR_SPRITE ())
    c4d.plugins.RegisterCommandPlugin (AI_C_DIR_RENDERS , "Renders"            , 134217728 | 268435456 , ico("folder") , "",   C_DIR_RENDERS ())

    c4d.plugins.RegisterCommandPlugin (AI_AIREN_4D_MENU , "Airen 4D"           , 134217728             , ico("render"), "", C_AI_AIREN_4D_MENU ())