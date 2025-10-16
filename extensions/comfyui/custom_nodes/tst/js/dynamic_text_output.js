import { app } from "../../scripts/app.js";

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
