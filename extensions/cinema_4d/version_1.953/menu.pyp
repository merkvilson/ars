import c4d
from c4d import gui

AI_RENDER_WINDOW = 1062009
AI_SKY           = 1062670
AI_TEXTURE       = 1099002
AI_SCENE_PROMPT  = 1062671
AI_BG            = 1062674
AI_MATERIAL      = 1062673
AI_PARAMETRIC_P  = 1062672

AI_INTER_TAG_CMD = 1062699


AI_AUDIO_TAG     = 1062698
AI_AUDIO_OBJ     = 1062692

AI_VOICE_OBJ_CMD    = 1062685
AI_SOUNDFX_OBJ_CMD  = 1062691
AI_SONG_OBJ_CMD     = 1062690
AI_MUSIC_OBJ_CMD    = 1062686

AI_VOICE_TAG_CMD    = 1062697
AI_SOUNDFX_TAG_CMD  = 1062687
AI_SONG_TAG_CMD     = 1062688
AI_MUSIC_TAG_CMD    = 1062689
AI_TERRAIN_GEN      = 1062684 
AI_C_Par_RndPick    = 1062683
AI_C_Par_LOD        = 1062682
AI_C_Par_Prompt     = 1062681
AI_C_Par_Morph      = 1062680
AI_C_Par_Time       = 1062679
AI_C_Par_Season     = 1062678
AI_C_Par_LORA       = 1062937
AI_3D               = 1062936
AI_SPRITE           = 1063090

AI_C_DIR_BG      = 1063089
AI_C_DIR_DOME    = 1063088
AI_C_DIR_TEX     = 1063087
AI_C_DIR_TERRAIN = 1063086
AI_C_DIR_SPRITE  = 1063085
AI_C_DIR_RENDERS = 1063084


def __(bc): bc.InsData(2, True)


def EnhanceMainMenu():
    mainMenu = gui.GetMenuResource("M_EDITOR")                 
    pluginsMenu = gui.SearchPluginMenuResource()               


    main_bc = c4d.BaseContainer()     

    main_bc.InsData(c4d.MENURESOURCE_SUBTITLE, "Airen 4D") 

    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_RENDER_WINDOW}"); __(main_bc)
    

    modifiers_bc = c4d.BaseContainer()
    modifiers_bc.InsData(c4d.MENURESOURCE_SUBTITLE, "Modifiers")
    modifiers_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_Par_RndPick}")
    modifiers_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_Par_LOD    }")
    modifiers_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_Par_Prompt }")
    modifiers_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_Par_Morph  }")
    modifiers_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_Par_Time  }")
    modifiers_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_Par_Season  }")
    modifiers_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_Par_LORA  }")
    main_bc.InsData(c4d.MENURESOURCE_SUBMENU, modifiers_bc)
    __(main_bc)



    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_MATERIAL}")     
    __(main_bc)

    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_SCENE_PROMPT}")     
    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_SKY}")     
    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_BG}")     
    __(main_bc)

    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_3D}")     
    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_TERRAIN_GEN}")     
    main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_SPRITE}")     
    __(main_bc)
    
    #main_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_INTER_TAG_CMD}")     
    #__(main_bc)


    audio_bc = c4d.BaseContainer()
    audio_bc.InsData(c4d.MENURESOURCE_SUBTITLE, "Audio")
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_VOICE_OBJ_CMD}")
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_SOUNDFX_OBJ_CMD}")
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_SONG_OBJ_CMD}")
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_MUSIC_OBJ_CMD}")
    __(audio_bc)
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_VOICE_TAG_CMD}")     
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_SOUNDFX_TAG_CMD}")     
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_SONG_TAG_CMD}")     
    audio_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_MUSIC_TAG_CMD}")     

    main_bc.InsData(c4d.MENURESOURCE_SUBMENU, audio_bc)

    paths_bc = c4d.BaseContainer()
    paths_bc.InsData(c4d.MENURESOURCE_SUBTITLE, "Directories")
    paths_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_DIR_BG      }")
    paths_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_DIR_DOME    }")
    paths_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_DIR_TEX     }")
    paths_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_DIR_TERRAIN }")
    paths_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_DIR_SPRITE  }")
    paths_bc.InsData(c4d.MENURESOURCE_COMMAND, f"PLUGIN_CMD_{AI_C_DIR_RENDERS }")
    main_bc.InsData(c4d.MENURESOURCE_SUBMENU, paths_bc)






    if pluginsMenu: mainMenu.InsDataAfter(c4d.MENURESOURCE_STRING, main_bc, pluginsMenu)
    else: mainMenu.InsData(c4d.MENURESOURCE_STRING, main_bc)

def PluginMessage(id, data):
    if id==c4d.C4DPL_BUILDMENU:
        EnhanceMainMenu()