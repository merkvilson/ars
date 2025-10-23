import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *
from c4d_gui_cmd import *


class OAI_3D(c4d.plugins.ObjectData):

    def __init__(self) :

        self.bmp = c4d.bitmaps.BaseBitmap()
        self.img_dir = sd_2d_dir


    def Init(self, node):

        apply_defaults(node, "mesh")

        #apply_last_image(node, self.img_dir)

        return True



    def GetDDescription(self, node, description, flags):

        if not description.LoadDescription(c4d.Obase): return False

        settings_tab = c4d.DescID(c4d.DescLevel(1100, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "Settings")
        bc.SetInt32(c4d.DESC_COLUMNS, 1)
        if not description.SetParameter(settings_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  ):
            return False

        prompt_frame(node, description, c4d.ID_OBJECTPROPERTIES)
        #thumb_frame(node, description, c4d.ID_OBJECTPROPERTIES, self.img_dir)
        adv_tab = adv_tab_frame(node, description)

        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)



    def Message(self, node, type, data):


        if type == c4d.MSG_MENUPREPARE:
            print('Object Created')

        if type == c4d.MSG_DESCRIPTION_CHECKUPDATE:


            desc_id = data["descid"][0].id

            prompt_frame_msg(desc_id, node)


            if desc_id in [RNDR_PREV_SEED,RNDR_CRNT_SEED,RNDR_NEXT_SEED,]:

                render_simple_prompt(node, "3d.json", "3d/mesh")

                return True



            if desc_id == GENERATE_OBJ3D:

                print("Creatring 3D object")


        if type == c4d.MSG_DESCRIPTION_GETBITMAP:
            return MSG_DESCRIPTION_GETBITMAP_msg(data, self.img_dir, node)

        return True

    def GetDEnabling(self, node, id, t_data, flags, itemdesc):
        
        if id[0].id in [CLEAR_PROMPTS_,IMAGE_QUALITY_,GENERATE_BUTTON,POSITIVE_PROMPT]:  return bool(os.listdir(sd_triposr_path))
        elif id[0].id in [RNDR_PREV_SEED,RNDR_CRNT_SEED,RNDR_NEXT_SEED,SAVE_IMAGE,GENERATE_OBJ3D,]: return bool(node[GENERATE_BUTTON])
        return True


    def GetDParameter(self, node, id, flags):

        return GetDParameter_thumbs_MSG(id[0].id, self.bmp, flags, node, id, self.img_dir)



    def GetVirtualObjects(self, op, hh):
        final_ptompt_update(op)
        return None
