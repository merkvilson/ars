
import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "custom.DynamicTextOutput",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "DynamicTextOutput") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated?.apply(this, arguments);
                
                this.outputCount = 1;
                this.addTextInput(0);
                this.addOutput(`output_0`, "STRING");
                
                // Add the "add_output" button
                const addButton = this.addWidget("button", "add_output", null, () => {
                    const idx = this.outputCount;
                    this.addTextInput(idx);
                    this.addOutput(`output_${idx}`, "STRING");
                    this.outputCount++;
                    this.setSize(this.computeSize());
                });
                
                return result;
            };
            
            nodeType.prototype.addTextInput = function(idx) {
                const widget = ComfyWidgets.STRING(this, `text_${idx}`, ["STRING", { 
                    default: "",
                    multiline: false
                }], app).widget;
                widget.inputEl.placeholder = `Text ${idx}`;
                return widget;
            };
        }
    }
});
