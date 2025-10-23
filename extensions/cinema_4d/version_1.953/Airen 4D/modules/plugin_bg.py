import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *

from c4d_gui_cmd import *



class OSceneBG(c4d.plugins.ObjectData):

    def __init__(self) :

        self.bmp = c4d.bitmaps.BaseBitmap()

        return None


    def Init(self, node, isCloneInit=False):


        if node.CheckType(AI_SKY):
            self.dir = sd_dome_dir
            apply_defaults(node, "dome")
        
        if node.CheckType(AI_BG):
            self.dir = sd_bg_dir
            apply_defaults(node, "bg")



        apply_last_image(node, self.dir)


        return True


    def GetDDescription(self, node, description, flags):

        data = node.GetDataInstance()
        node_tp = node.GetType()
        if not description.LoadDescription(node_tp): return False

        settings_tab = c4d.DescID(c4d.DescLevel(1100, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "Settings")
        bc.SetInt32(c4d.DESC_COLUMNS, 1)
        if not description.SetParameter(settings_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  ):
            return False


        prompt_frame(node, description, c4d.ID_OBJECTPROPERTIES)
        thumb_frame(node, description, c4d.ID_OBJECTPROPERTIES, self.dir)
        adv_tab_frame(node, description)


        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)


    def GetDEnabling(self, node, id, t_data, flags, itemdesc):
        if id[0].id == GENERATE_BUTTON: return bool(node[GENERATE_BUTTON])
        return True

    def GetDParameter(self, node, id, flags):
        return GetDParameter_thumbs_MSG(id[0].id, self.bmp, flags, node, id, self.dir)



    def Message(self, node, type, data):

        
        if type == c4d.MSG_DESCRIPTION_CHECKUPDATE:

            desc_id = data["descid"][0].id

            prompt_frame_msg(desc_id, node)
            thumbnail_dropdown_msg(desc_id, node, self.dir)

            if desc_id in [RNDR_PREV_SEED,RNDR_CRNT_SEED,RNDR_NEXT_SEED,]:


                prefix = "HDRI" if node.CheckType(AI_SKY) else "Background" #TODO: Sometimes HDRI is better  than latentlabs360
                width = node[IMAGE_WIDTH]
                height = node[IMAGE_HEIGHT]


                render_simple_prompt(node, "bg.json", "steps/bg")

                return True

            if desc_id >= 5000:
                try:node.GetDown().GetTag(c4d.Ttexture)[c4d.TEXTURETAG_MATERIAL][c4d.MATERIAL_LUMINANCE_SHADER][c4d.BITMAPSHADER_FILENAME] = node[IMAGE_PATH]
                except: pass

            if desc_id == IMAGE_WIDTH:
                if node.CheckType(AI_SKY):
                    node[IMAGE_HEIGHT] = int(node[IMAGE_WIDTH] / 2)


            elif desc_id == IMAGE_HEIGHT:
                if node.CheckType(AI_SKY):
                    node[IMAGE_WIDTH] = int(node[IMAGE_HEIGHT] * 2)



        if type == c4d.MSG_DESCRIPTION_GETBITMAP:
            return MSG_DESCRIPTION_GETBITMAP_msg(data, self.dir, node)




        # if type == c4d.MSG_UPDATE:
        #     try:
        #         img = node[IMAGE_PATH]
        #         if node[1007][0] == " ": img = os.path.join(sd_steps_path, os.listdir(sd_steps_path)[-1])
        #         node.GetDown().GetTag(c4d.Ttexture)[c4d.TEXTURETAG_MATERIAL][c4d.MATERIAL_LUMINANCE_SHADER][c4d.BITMAPSHADER_FILENAME] = img
        #     except: pass


        if type == c4d.MSG_MENUPREPARE:


            if find_obj(node.GetType()): 
                node.ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)
                return True

            doc = c4d.documents.GetActiveDocument()



            bg = c4d.BaseObject(c4d.Osky if node.CheckType(AI_SKY) else c4d.Obackground)
            bg.InsertUnder(node)

            MAT_NAME = "AIREN_SKY" if node.CheckType(AI_SKY) else "AI_BG"


            materials = doc.GetMaterials()

            if MAT_NAME in [mat.GetName() for mat in doc.GetMaterials()]: return

            material = c4d.BaseMaterial(c4d.Mmaterial)
            material.SetName(MAT_NAME)

            texture_input = c4d.BaseShader(c4d.Xbitmap)
            material.InsertShader(texture_input)

            material[c4d.MATERIAL_USE_COLOR]        = False
            material[c4d.MATERIAL_USE_REFLECTION]   = False
            material[c4d.MATERIAL_USE_LUMINANCE]    = True
            material[c4d.MATERIAL_PREVIEWSIZE]      = True
            material[c4d.MATERIAL_LUMINANCE_SHADER] = texture_input

            # Insert the material into the document
            doc = c4d.documents.GetActiveDocument()
            doc.InsertMaterial(material)

            texture_input.Message(c4d.MSG_UPDATE)
            material.Message(c4d.MSG_UPDATE)
            material.Update(True, True)


            material_tag = bg.MakeTag(c4d.Ttexture)
            material_tag[c4d.TEXTURETAG_MATERIAL] = material
            material_tag[c4d.TEXTURETAG_PROJECTION] = 0 if node.CheckType(AI_SKY) else 4

            material    .ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)
            material_tag.ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)
            bg          .ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)

            node.ChangeNBit(c4d.NBIT_OM1_FOLD, c4d.NBITCONTROL_SET)
            node.ChangeNBit(c4d.NBIT_OM2_FOLD, c4d.NBITCONTROL_SET)
            node.ChangeNBit(c4d.NBIT_OM3_FOLD, c4d.NBITCONTROL_SET)
            node.ChangeNBit(c4d.NBIT_OM4_FOLD, c4d.NBITCONTROL_SET)


            node.GetDown().GetTag(c4d.Ttexture)[c4d.TEXTURETAG_MATERIAL][c4d.MATERIAL_LUMINANCE_SHADER][c4d.BITMAPSHADER_FILENAME] = node[IMAGE_PATH]


        return True


    def GetVirtualObjects(self, op, hh):
        final_ptompt_update(op)
        return None