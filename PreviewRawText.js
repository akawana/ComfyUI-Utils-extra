import { app } from "../../scripts/app.js";

(function () {
    app.registerExtension({
        name: "PreviewRawTextExtension",
        beforeRegisterNodeDef(nodeType, nodeData, appInstance) {
            if (nodeData.name !== "PreviewRawText") return;

            const origOnNodeCreated = nodeType.prototype.onNodeCreated;
            const origOnDrawForeground = nodeType.prototype.onDrawForeground;

            nodeType.prototype.onNodeCreated = function () {
                const node = this;
                origOnNodeCreated && origOnNodeCreated.apply(node, arguments);

                // Add read-only multiline widget for preview
                const existing =
                    node.widgets && node.widgets.find((w) => w.name === "preview_raw");
                if (!existing) {
                    const w = node.addWidget(
                        "text",
                        "preview_raw",
                        "",
                        null,
                        { multiline: true }
                    );
                    w.readonly = true;
                    node._previewRawWidget = w;
                }
            };

            // Мы не можем полагаться на onExecuted() для STRING,
            // поэтому каждый кадр читаем текст из входного нода.
            nodeType.prototype.onDrawForeground = function (ctx) {
                const node = this;
                if (origOnDrawForeground) {
                    origOnDrawForeground.apply(node, arguments);
                }

                const w =
                    node._previewRawWidget ||
                    (node.widgets &&
                        node.widgets.find((w) => w.name === "preview_raw"));

                if (!w) return;

                let value = "";

                // Берём первую входную ноду (slot 0)
                if (node.inputs && node.inputs.length > 0) {
                    const inputSlot = node.inputs[0];
                    const inputName = inputSlot.name || "text";

                    if (typeof node.getInputNode === "function") {
                        const srcNode = node.getInputNode(0);
                        if (srcNode && srcNode.widgets && srcNode.widgets.length > 0) {
                            // Пытаемся найти виджет с тем же именем, что и вход
                            let srcWidget =
                                srcNode.widgets.find((w) => w.name === inputName) ||
                                srcNode.widgets.find((w) => w.name === "text");

                            if (srcWidget && typeof srcWidget.value === "string") {
                                value = srcWidget.value;
                            }
                        }
                    }
                }

                if (w.value !== value) {
                    w.value = value;
                    node.setDirtyCanvas(true, true);
                }
            };
        },
    });
})();
