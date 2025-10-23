import c4d
from generate    import *
from airen_paths import *
from c4d_gui     import *
from plugin_ids  import *
from airen_cmds  import *
from airen_vars  import *
from c4d_gui_fr  import *
from c4d_gui_cmd import *


class Opprompt(c4d.plugins.ObjectData): 

    def Init(self, node):

        apply_defaults(node, "pprompt")

        self.types = ['Parametric Prompt', 'Level Of Details', "Random Picker", "Prompt Morph", "Time", "Season", "Lora"]
        
        if os.listdir(ai_paths_cmd("loras")): self.loras_raw = [lora[:-12] for lora in os.listdir(ai_paths_cmd("loras"))]
        else: self.loras_raw = [' ']
        self.loras =  [lora.replace("_"," ").title() for lora in self.loras_raw]

        return True

    def GetDDescription(self, node, description, flags):
        data = node.GetDataInstance()
        node_tp = node.GetType()

        if not description.LoadDescription(node_tp): return False

        settings_tab = c4d.DescID(c4d.DescLevel(1100, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "Settings")
        bc.SetInt32(c4d.DESC_COLUMNS, 1)
        description.SetParameter(settings_tab, bc, c4d.DescID(c4d.DescLevel((node.GetType())))  )

        input_field(node, description, PARAMETRIC_OUTPUT, "Output",   group = settings_tab, multiline = False)
        dropdown  (node, description, index = PARAMETRIC_TYPE, name = "Type", ddef = 0,options = self.types, group = settings_tab )
        check_box  (description, NEG_POS_CHK, settings_tab, "Negative/Positive")

        hiding     (      description, 1100, node.GetName() != '123qwe')



        lora_frame = c4d.DescID(c4d.DescLevel(LORA_FRAME, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "")
        bc.SetInt32(c4d.DESC_COLUMNS, 3)
        description.SetParameter(lora_frame, bc, c4d.ID_OBJECTPROPERTIES  )
        
        dropdown  (node, description, index = LORA_DROPDOWN, name = "Lora", ddef = 0,options = self.loras, group = LORA_FRAME )
        static_text(node, description, LORA_FRAME, True,  id = 1)
        quick_commands (node, description, CUSTOM_SETTINGS_, group = LORA_FRAME, img = 1062906, tooltip = "Settings", size = 25)
        hiding     (      description, LORA_FRAME, node[PARAMETRIC_TYPE] != 6)


        input_field(node, description, LORA_KEYWORDS, "Key Words",   group = c4d.ID_OBJECTPROPERTIES, multiline = False)
        hiding     (      description, LORA_KEYWORDS, node[PARAMETRIC_TYPE] != 6)


        input_field(node, description, PARAMETRIC_PROMPT, "Prompt",   group = c4d.ID_OBJECTPROPERTIES, multiline = False)
        hiding     (      description, PARAMETRIC_PROMPT, node[PARAMETRIC_TYPE] in [1,3,4,6])

        input_field(node, description, PARAMETRIC_PROMPT_A, "Input A",   group = c4d.ID_OBJECTPROPERTIES, multiline = False)
        input_field(node, description, PARAMETRIC_PROMPT_B, "Input B",   group = c4d.ID_OBJECTPROPERTIES, multiline = False)
        hiding     (      description, PARAMETRIC_PROMPT_A, node[PARAMETRIC_TYPE] != 3)
        hiding     (      description, PARAMETRIC_PROMPT_B, node[PARAMETRIC_TYPE] != 3)




        clock_group = c4d.DescID(c4d.DescLevel(11700, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "")
        bc.SetInt32(c4d.DESC_COLUMNS, 5)
        if not description.SetParameter(clock_group, bc, c4d.ID_OBJECTPROPERTIES  ):
            return False
        

        separator_line(description, True, clock_group, t_id = 51223)
        separator_line(description, 0, clock_group, t_id = 51224)
        separator_line(description, 0, clock_group, t_id = 51225)
        separator_line(description, 0, clock_group, t_id = 51227)
        separator_line(description, 0, clock_group, t_id = 51228)
        separator_line(description, 0, clock_group, t_id = 51229)

        date_time_clock(description, PARAMETRIC_AM_PM, clock_group, "", 1,1)
        hiding         (description, 11700, node[PARAMETRIC_TYPE] != 4)
        # date_time_clock(description, PARAMETRIC_DATE , clock_group, "", 0,1)
        # hiding         (description, 11700, node[PARAMETRIC_TYPE] != 5)



        clock_group1 = c4d.DescID(c4d.DescLevel(11701, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "")
        bc.SetInt32(c4d.DESC_COLUMNS, 8)
        if not description.SetParameter(clock_group1, bc, clock_group  ):
            return False

        separator_line(description, True, clock_group, t_id = 51274)




        weight_frame = c4d.DescID(c4d.DescLevel(WEIGHT_FRAME, c4d.DTYPE_GROUP, node.GetType()))
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)
        bc.SetString(c4d.DESC_NAME, "")
        bc.SetInt32(c4d.DESC_COLUMNS, 3)
        description.SetParameter(weight_frame, bc, c4d.ID_OBJECTPROPERTIES  )
        
        float_slider(node, description, PARAMETRIC_INFLUENCE, "Weight", 1, WEIGHT_FRAME, -1)
        static_text(node, description, WEIGHT_FRAME, True,  id = 663)
        if node[NEG_POS_CHK]: quick_commands (node, description, NEG_POS_BTN, group = WEIGHT_FRAME, img = 1062932, tooltip = "Mode", size = 25, )
        else: quick_commands (node, description, NEG_POS_BTN, group = WEIGHT_FRAME, img = 1062931, tooltip = "Mode", size = 25, )



        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)


    def Message(self, node, type, data):

        if type == c4d.MSG_MENUPREPARE:
            c4d.CallCommand(100004708)


        if type == c4d.MSG_DESCRIPTION_CHECKUPDATE:

            desc_id = data["descid"][0].id

            name_to_msg(desc_id, node)

            output = ""
            influence = node[PARAMETRIC_INFLUENCE]

            icons_path = os.path.join(plugin_path, 'res', 'Icons')

            if self.types[node[PARAMETRIC_TYPE]] == 'Level Of Details':  
                output =  f'<lora:add_detail:{round(influence * 3, 3)}>'
                if   influence < -0.5: lod_icon = '1063050'
                elif influence >  0.5: lod_icon = '1063052'
                else:                  lod_icon = '1063051'
                node[c4d.ID_BASELIST_ICON_FILE] = lod_icon
            
            elif self.types[node[PARAMETRIC_TYPE]] == 'Parametric Prompt': 
                output =  f'({  node[PARAMETRIC_PROMPT]                              }:{round(influence * 2, 3)})'
                node[c4d.ID_BASELIST_ICON_FILE] = '1063055'
            
            elif self.types[node[PARAMETRIC_TYPE]] == 'Random Picker':     
                output =  f'({  random.choice( (node[PARAMETRIC_PROMPT]).split(","))  }:{round(influence * 2, 3)})'
                node[c4d.ID_BASELIST_ICON_FILE] = '1063056'
                        
            elif self.types[node[PARAMETRIC_TYPE]] == 'Time':     
                output =  f'({  random.choice( ["day", "night", "morning", "sunset"] )  }:{round(influence * 2, 3)})'
                node[c4d.ID_BASELIST_ICON_FILE] = '1063058'
                                    
            elif self.types[node[PARAMETRIC_TYPE]] == 'Season':     
                output =  f'({  random.choice( ["day", "night", "morning", "sunset"] )  }:{round(influence * 2, 3)})'
                node[c4d.ID_BASELIST_ICON_FILE] = '1063057'
                # dt = op[c4d.SKY_DATE_TIME].GetDateTime()
                # dtd = c4d.DateTimeData()
                # dtd.SetDateTime(dt)

                # t = dtd.GetDateTime()
                # print(t.day)
                # print(t.month)
                # print(t.year)
                # print(t.hour)
                # print(t.minute)
                # print(t.second)


            
            elif self.types[node[PARAMETRIC_TYPE]] == 'Prompt Morph':     
                output =  f'[{node[PARAMETRIC_PROMPT_B]}:{node[PARAMETRIC_PROMPT_A]}:{round(c4d.utils.RangeMap(value=influence, mininput=-1, maxinput=1, minoutput=0.0, maxoutput=1.0, clampval=True),1)}]'
                node[c4d.ID_BASELIST_ICON_FILE] = '1063054'
            
            elif self.types[node[PARAMETRIC_TYPE]] == 'Lora':

                if os.listdir(ai_paths_cmd("loras")):
                    output =  f'<lora:{self.loras_raw[node[LORA_DROPDOWN]]}:{round(influence, 3)}>'
                    if node[LORA_KEYWORDS]: output = f'{node[LORA_KEYWORDS]}, {output}'
                    node[c4d.ID_BASELIST_ICON_FILE] = '1063053'



            if output: 
                node[PARAMETRIC_OUTPUT] = output

            if desc_id == PARAMETRIC_TYPE:
                node.SetName(self.types[node[PARAMETRIC_TYPE]])


            elif desc_id == NEG_POS_BTN:
                node[NEG_POS_CHK] = not node[NEG_POS_CHK]


            elif desc_id == CUSTOM_SETTINGS_:
                def check_r(value):
                    if value: return "&c&"
                    else: return ""

                n = c4d.FIRST_POPUP_ID
                bc = c4d.BaseContainer()
                LORA_RELOAD
                LORA_INSTALL
                LORA_FOLDER

                bc.InsData(n+0, f'Reload Lora    &i{1062934}&{check_r(False)}')
                bc.InsData(n+1, f'Install Lora   &i{1063092}&{check_r(False)}')
                bc.InsData(n+2, f'Open Directory &i{1062904}&{check_r(False)}')
                
                key_bc = c4d.BaseContainer()
                if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.BFM_INPUT_CHANNEL, key_bc):

                    result = c4d.gui.ShowPopupDialog(None, bc,2147483647,2147483647, )
                    
                    if result == n+0:   #Reload Lora
                        node.SetDirty(c4d.DIRTYFLAGS_ALL)


                    elif result == n+1:     #Install Lora
                        new_lora = c4d.storage.LoadDialog(type=c4d.FILESELECTTYPE_ANYTHING, title='Select Lora', flags=c4d.FILESELECT_LOAD, force_suffix='safetensors', def_path='', def_file='')
                        if new_lora:
                            if new_lora.endswith('safetensors'):
                                shutil.move(new_lora, ai_paths_cmd("loras"))



                    elif result == n+2:     #Open Directory
                        subprocess.Popen(['explorer', ai_paths_cmd("loras")])


                    self.loras_raw = [lora[:-12] for lora in os.listdir(ai_paths_cmd("loras"))]
                    self.loras     = [lora.replace("_"," ").title() for lora in self.loras_raw]
                    node.SetDirty(c4d.DIRTYFLAGS_ALL)             

        return True


    def GetVirtualObjects(self, node, hh):

        if c4d.CheckIsRunning(c4d.CHECKISRUNNING_VIEWDRAWING):
            if self.types[node[PARAMETRIC_TYPE]] == 'Random Picker': 
                influence = round(node[PARAMETRIC_INFLUENCE],3)
                output =  f'({  random.choice((node[PARAMETRIC_PROMPT]).split(","))  }:{influence})'
                node[PARAMETRIC_OUTPUT] = output

        return None