import os

plugin_path       = os.path.dirname(os.path.split(__file__)[0])
airen_root_path   = os.path.dirname(os.path.dirname(os.path.dirname(plugin_path)))
airen_models_path = os.path.join (airen_root_path ,"AIREN_MODELS")

airen_custom_nodes_path = os.path.join(plugin_path, "res", "airen_custom_nodes")

for nec_dir in ["checkpoints", "loras", "controlnet"]:
	os.makedirs(os.path.join(airen_models_path, nec_dir), exist_ok=True)


def ai_paths_cmd(model_type):
    model_type_path = os.path.join (airen_models_path , model_type)
    return model_type_path


os.makedirs(os.path.join (airen_root_path ,"CUI"), exist_ok=True)


user_comfy_ui      = os.listdir (os.path.join (airen_root_path ,"CUI"))[0]

comfyui_path      = os.path.join (airen_root_path ,"CUI", user_comfy_ui, "ComfyUI")


comfyui_log_path  = os.path.join (airen_root_path ,"CUI", user_comfy_ui, "comfyui.log")
comfyui_log2_path = os.path.join (airen_root_path ,"CUI", user_comfy_ui, "comfyui2.log")

extra_model_yaml = os.path.join(comfyui_path, "extra_model_paths.yaml")


sd_cstnodes_path  = os.path.join(comfyui_path, "custom_nodes")
if not os.path.exists(sd_cstnodes_path ): os.mkdir(sd_cstnodes_path )


sd_output_path    = os.path.join (comfyui_path, "output"  )
if not os.path.exists(sd_output_path ): os.mkdir(sd_output_path )


sd_render_path    = os.path.join (comfyui_path, "input"  )

sd_lora_path      = os.path.join (comfyui_path, "models", "loras", "user" )
if not os.path.exists(sd_lora_path): os.mkdir(sd_lora_path)


sd_chpoint_path   = os.path.join (comfyui_path, "models", "checkpoints" )
if not os.path.exists(sd_chpoint_path): os.mkdir(sd_chpoint_path)


sd_steps_path     = os.path.join (sd_output_path  ,"steps"          ,)
if not os.path.exists(sd_steps_path  ): os.mkdir(sd_steps_path  )

sd_txt2img_path   = os.path.join (sd_output_path  ,"txt2img-images" ,)
if not os.path.exists(sd_txt2img_path): os.mkdir(sd_txt2img_path)

sd_depth4d_path   = os.path.join (sd_output_path  ,"depth4d"        ,)
if not os.path.exists(sd_depth4d_path): os.mkdir(sd_depth4d_path)

sd_tex_dir        = os.path.join (sd_output_path  ,"textures"       ,)
if not os.path.exists(sd_tex_dir     ): os.mkdir(sd_tex_dir     )

sd_terrain_dir    = os.path.join (sd_output_path  ,"terrain"        ,)
if not os.path.exists(sd_terrain_dir ): os.mkdir(sd_terrain_dir )

sd_dome_dir       = os.path.join (sd_output_path  ,"dome"           ,)
if not os.path.exists(sd_dome_dir    ): os.mkdir(sd_dome_dir    )

sd_bg_dir         = os.path.join (sd_output_path  ,"bg"             ,)
if not os.path.exists(sd_bg_dir      ): os.mkdir(sd_bg_dir      )

sd_3d_dir         = os.path.join (sd_output_path  ,"3d"             ,)
if not os.path.exists(sd_3d_dir      ): os.mkdir(sd_3d_dir      )

sd_2d_dir         = os.path.join (sd_output_path  ,"2d"             ,)
if not os.path.exists(sd_2d_dir      ): os.mkdir(sd_2d_dir      )

sd_saved_render   = os.path.join (sd_output_path  ,"saved renders"  ,)
if not os.path.exists(sd_saved_render): os.mkdir(sd_saved_render)

sd_sprite_dir     = os.path.join (sd_output_path  ,"sprites"        ,)
if not os.path.exists(sd_sprite_dir  ): os.mkdir(sd_sprite_dir  )