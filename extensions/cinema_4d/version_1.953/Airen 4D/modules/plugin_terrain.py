import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *
from c4d_gui_cmd import *


class OAi_Terrain(c4d.plugins.ObjectData):

    def __init__(self) :

        self.bmp = c4d.bitmaps.BaseBitmap()


    def Init(self, node):

        apply_defaults(node, "terrain")
        apply_last_image(node, sd_terrain_dir)
        return True


    def GetHandleCount(self, op):
        return 1

    def GetHandle(self, op, i, info):
        data = op.GetDataInstance()
        if data is None: return

        info.position = c4d.Vector(0, data[DISPLACER_HEIGHT], 0)
        info.direction = c4d.Vector(0,1,0)
        info.type = c4d.HANDLECONSTRAINTTYPE_LINEAR


    def SetHandle(self, op, i, p, info):
        data = op.GetDataInstance()
        if data is None: return
        
        val = p*info.direction
        
        data.SetReal(DISPLACER_HEIGHT, val)

    def Draw(self, op, drawpass, bd, bh):
        if drawpass == c4d.DRAWPASS_HANDLES:

            bd.SetMatrix_Matrix(None, bh.GetMg())

            info = c4d.HandleInfo()
            self.GetHandle(op, 1, info)

            bd.SetPen(c4d.GetViewColor(c4d.VIEWCOLOR_ACTIVEPOINT))

            bd.DrawArc(info.position, 3, r(0), r(360))

            bd.DrawLine(info.position, c4d.Vector(0), 0)

            c4d.plugins.ObjectData.Draw(self, op, drawpass, bd, bh)

        return c4d.DRAWRESULT_OK



    def GetDDescription(self, node, description, flags):

        if not description.LoadDescription(c4d.Obase): return False

        settings_tab = c4d.DescID(c4d.DescLevel(1100, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "Settings")
        bc.SetInt32(c4d.DESC_COLUMNS, 1)
        if not description.SetParameter(settings_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  ):
            return False

        prompt_frame(node, description, c4d.ID_OBJECTPROPERTIES)
        thumb_frame(node, description, c4d.ID_OBJECTPROPERTIES, sd_terrain_dir)
        adv_tab = adv_tab_frame(node, description)
        
        slider(node, description, DISPLACER_HEIGHT, "Height", 100, adv_tab , minslider = 0)

        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)


    def Message(self, node, type, data):
        if type == c4d.MSG_MENUPREPARE:

            plane = c4d.BaseObject(c4d.Oplane)
            plane[c4d.PRIM_PLANE_SUBW] = 100
            plane[c4d.PRIM_PLANE_SUBH] = 100
            plane.InsertUnder(node)
            phong = plane.MakeTag(c4d.Tphong)
            phong[c4d.PHONGTAG_PHONG_ANGLELIMIT] = False

            #plane.ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)
            node.ChangeNBit(c4d.NBIT_OM1_FOLD, c4d.NBITCONTROL_SET)
            node.ChangeNBit(c4d.NBIT_OM2_FOLD, c4d.NBITCONTROL_SET)
            node.ChangeNBit(c4d.NBIT_OM3_FOLD, c4d.NBITCONTROL_SET)
            node.ChangeNBit(c4d.NBIT_OM4_FOLD, c4d.NBITCONTROL_SET)
            print('Object Created')

        if type == c4d.MSG_DESCRIPTION_CHECKUPDATE:

            desc_id = data["descid"][0].id

            prompt_frame_msg(desc_id, node)
            thumbnail_dropdown_msg(desc_id, node, sd_terrain_dir)


            if desc_id in [RNDR_PREV_SEED,RNDR_CRNT_SEED,RNDR_NEXT_SEED,]:

                prefix = ""
                prefix += '<lora:Hight Map_V03:1>, BW, Hight Map, ' if node[LORA_HEIGHT] else "" 

                print("Terrain _ TODO!!!!!!!!!!!!!!!!")


        if type == c4d.MSG_DESCRIPTION_GETBITMAP:

            return MSG_DESCRIPTION_GETBITMAP_msg(data, sd_terrain_dir, node)

        return True


    def GetDParameter(self, node, id, flags):

        return GetDParameter_thumbs_MSG(id[0].id, self.bmp, flags, node, id, sd_terrain_dir)


    def GetVirtualObjects(self, op, hh):
        final_ptompt_update(op)
        orig = op.GetDown()
        doc = op.GetDocument()
        if orig is None: return None

        gch      = op.GetAndCheckHierarchyClone(hh=hh, op=orig, allchildren=True, flags = c4d.HIERARCHYCLONEFLAGS_ASPOLY, )
        dirty    = gch['dirty']
        clone    = gch['clone']

        if not dirty: return clone
        if clone is None: return None

        disp = c4d.BaseObject(1018685)


        texture_input = c4d.BaseShader(c4d.Xbitmap)
        disp.InsertShader(texture_input)
        disp[c4d.ID_MG_SHADER_SHADER] = texture_input
        disp[c4d.ID_MG_SHADER_SHADER][c4d.BITMAPSHADER_FILENAME] = op[IMAGE_PATH]
        disp[c4d.MGDISPLACER_DISPLACEMENT_HEIGHT] = op[DISPLACER_HEIGHT]
        texture_input.Message(c4d.MSG_UPDATE)

        sds = c4d.BaseObject(c4d.Osds)
        sds[c4d.SDSOBJECT_TYPE]=2109
        # display_tag = clone.MakeTag(5613)
        # display_tag[c4d.DISPLAYTAG_AFFECT_DISPLAYMODE] = True
        # display_tag[c4d.DISPLAYTAG_SDISPLAYMODE] = doc.GetActiveBaseDraw()[c4d.BASEDRAW_DATA_SDISPLAYACTIVE]
        # display_tag[c4d.DISPLAYTAG_WDISPLAYMODE] = 1

        disp.InsertUnder(sds)
        clone.InsertUnder(sds)

        return sds
