import os
import folder_paths

class DynamicTextOutputNode:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_0": ("STRING", {"default": "", "multiline": False}),
            },
            "hidden": {
                "output_count": "INT",
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_0",)
    FUNCTION = "process"
    CATEGORY = "custom"
    OUTPUT_IS_LIST = (True,)
    
    def process(self, text_0, output_count=1, **kwargs):
        outputs = [text_0]
        
        # Collect additional text inputs if they exist
        for i in range(1, output_count):
            text_key = f"text_{i}"
            if text_key in kwargs:
                outputs.append(kwargs[text_key])
        
        return (outputs,)

NODE_CLASS_MAPPINGS = {
    "DynamicTextOutput": DynamicTextOutputNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DynamicTextOutput": "Dynamic Text Output"
}

# Set up web directory
WEB_DIRECTORY = "./js"

# Create js directory and file
current_dir = os.path.dirname(os.path.abspath(__file__))
js_dir = os.path.join(current_dir, "js")
os.makedirs(js_dir, exist_ok=True)

js_code = """import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "custom.DynamicTextOutput",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "DynamicTextOutput") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                this.outputCount = 1;
                
                // Add button widget
                this.addWidget("button", "add_output", null, () => {
                    this.outputCount++;
                    const idx = this.outputCount - 1;
                    
                    // Add new input widget
                    this.addWidget("text", `text_${idx}`, "", () => {}, {});
                    
                    // Add new output
                    this.addOutput(`output_${idx}`, "STRING");
                    
                    // Update hidden output_count value
                    const countWidget = this.widgets.find(w => w.name === "output_count");
                    if (countWidget) {
                        countWidget.value = this.outputCount;
                    }
                    
                    this.setSize(this.computeSize());
                });
                
                return r;
            };
        }
    }
});
"""

js_file = os.path.join(js_dir, "dynamic_text_output.js")
with open(js_file, "w", encoding="utf-8") as f:
    f.write(js_code)

print(f"[DynamicTextOutput] Node registered. JS file created at: {js_file}")