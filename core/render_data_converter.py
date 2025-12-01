def get_new_id(workflow):
    ids = [int(k) for k in workflow.keys() if k.isdigit()]
    return str(max(ids) + 1) if ids else "1"

def create_airen_gui_data(ud_name, output, symbol, additional_text, slider_values):
    return {
        "inputs": {
            "ud_name": ud_name,
            "data_type": "Integer",
            "output": output,
            "symbol": symbol,
            "additional_text": additional_text,
            "slider_values": slider_values
        },
        "class_type": "Airen_Gui_Data",
        "_meta": {
            "title": "Airen_Gui_Data"
        }
    }

def is_connected_to_airen(workflow, node_id, input_name):
    node = workflow.get(node_id)
    if not node: return False
    inp = node.get("inputs", {}).get(input_name)
    if isinstance(inp, list) and len(inp) == 2:
        source_id = str(inp[0])
        source_node = workflow.get(source_id)
        if source_node and source_node.get("class_type") == "Airen_Gui_Data":
            return True
    return False

def convert_KSampler(workflow):
    # Find KSampler nodes
    ksampler_ids = [k for k, v in workflow.items() if v.get("class_type") == "KSampler"]
    
    for kid in ksampler_ids:
        inputs = workflow[kid].get("inputs", {})
        
        # Steps
        if not is_connected_to_airen(workflow, kid, "steps"):
            current_val = inputs.get("steps")
            val_to_use = 20
            if isinstance(current_val, (int, float, str)) and not isinstance(current_val, list):
                 try:
                     val_to_use = int(current_val)
                 except:
                     pass
            
            steps_id = get_new_id(workflow)
            workflow[steps_id] = create_airen_gui_data("Steps", val_to_use, "ICON_STEPS", "Steps", "1,99,20")
            workflow[kid]["inputs"]["steps"] = [steps_id, 0]
        
        # Seed
        if not is_connected_to_airen(workflow, kid, "seed"):
            current_val = inputs.get("seed")
            val_to_use = 0
            if isinstance(current_val, (int, float, str)) and not isinstance(current_val, list):
                 try:
                     val_to_use = int(current_val)
                 except:
                     pass

            seed_id = get_new_id(workflow)
            workflow[seed_id] = create_airen_gui_data("Seed", val_to_use, "ICON_SEED_0", "Seed", "0,99999,1")
            workflow[kid]["inputs"]["seed"] = [seed_id, 0]

    # Find EmptyLatentImage nodes for Size
    latent_ids = [k for k, v in workflow.items() if v.get("class_type") == "EmptyLatentImage"]
    for lid in latent_ids:
        inputs = workflow[lid].get("inputs", {})
        # Check if width/height are already connected to Airen_Gui_Data
        # Usually width and height are connected to the same Size node in Airen workflow
        if not is_connected_to_airen(workflow, lid, "width"):
            current_width = inputs.get("width")
            val_to_use = 512
            if isinstance(current_width, (int, float, str)) and not isinstance(current_width, list):
                 try:
                     val_to_use = int(current_width)
                 except:
                     pass
            
            size_id = get_new_id(workflow)
            workflow[size_id] = create_airen_gui_data("Size", val_to_use, "ICON_GIZMO_SCALE", "Size", "48,1024,512")
            workflow[lid]["inputs"]["width"] = [size_id, 0]
            workflow[lid]["inputs"]["height"] = [size_id, 0]

def convert_Prompts(workflow):
    # Find KSampler nodes
    ksampler_ids = [k for k, v in workflow.items() if v.get("class_type") == "KSampler"]
    
    for kid in ksampler_ids:
        inputs = workflow[kid].get("inputs", {})
        
        # Get positive and negative inputs
        pos_link = inputs.get("positive")
        neg_link = inputs.get("negative")
        
        if not (isinstance(pos_link, list) and len(pos_link) == 2): continue
        if not (isinstance(neg_link, list) and len(neg_link) == 2): continue
        
        pos_id = str(pos_link[0])
        neg_id = str(neg_link[0])
        
        pos_node = workflow.get(pos_id)
        neg_node = workflow.get(neg_id)
        
        if not pos_node or not neg_node: continue
        
        # Check if they are CLIPTextEncode (or similar that takes text)
        if pos_node.get("class_type") != "CLIPTextEncode": continue
        if neg_node.get("class_type") != "CLIPTextEncode": continue
        
        # Check if already connected to Airen_Gui_Prompt
        # Check positive
        pos_inp = pos_node.get("inputs", {}).get("text")
        if isinstance(pos_inp, list) and len(pos_inp) == 2:
            src_node = workflow.get(str(pos_inp[0]))
            if src_node and src_node.get("class_type") == "Airen_Gui_Prompt":
                continue

        # Create Airen_Gui_Prompt
        prompt_id = get_new_id(workflow)
        
        # Extract existing text if available
        pos_text = pos_node["inputs"].get("text", "")
        if not isinstance(pos_text, str): pos_text = ""
        
        neg_text = neg_node["inputs"].get("text", "")
        if not isinstance(neg_text, str): neg_text = ""
        
        workflow[prompt_id] = {
            "inputs": {
                "ud_name": "prompt",
                "positive": pos_text,
                "negative": neg_text
            },
            "class_type": "Airen_Gui_Prompt",
            "_meta": {
                "title": "Airen_Gui_Prompt"
            }
        }
        
        # Connect
        pos_node["inputs"]["text"] = [prompt_id, 0]
        neg_node["inputs"]["text"] = [prompt_id, 1]

def replace_SaveImage(workflow):
    save_ids = [k for k, v in workflow.items() if v.get("class_type") == "SaveImage"]
    
    for sid in save_ids:
        old_node = workflow[sid]
        images_input = old_node["inputs"].get("images")
        
        # Replace with Airen_SaveImage
        workflow[sid] = {
            "inputs": {
                "ud_name": "",
                "category": "steps",
                "save_layers": True,
                "images": images_input
            },
            "class_type": "Airen_SaveImage",
            "_meta": {
                "title": "Airen_SaveImage"
            }
        }

def add_Airen_Gui_Defaults(workflow):
    # Check if exists
    for v in workflow.values():
        if v.get("class_type") == "Airen_Gui_Defaults":
            return

    # Add it
    defaults_id = get_new_id(workflow)
    workflow[defaults_id] = {
        "inputs": {
            "ud_name": "Default_Values",
            "workflow_type": "Image",
            "close_on_outside": False,
            "auto_close": False,
            "incremental_value": True,
            "show_value": True
        },
        "class_type": "Airen_Gui_Defaults",
        "_meta": {
            "title": "Airen_Gui_Defaults"
        }
    }
