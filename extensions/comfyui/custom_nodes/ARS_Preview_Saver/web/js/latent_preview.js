// ARS Preview Saver - Unified Latent Preview
import { app } from '../../../scripts/app.js'
import { api } from '../../../scripts/api.js'

function getNodeById(id, graph=app.graph) {
    let cg = graph
    let node = undefined
    for (let sid of (''+id).split(':')) {
        node = cg?.getNodeById?.(sid)
        cg = node?.subgraph
    }
    return node
}

let latentPreviewNodes = new Set()

app.registerExtension({
    name: 'ARS.PreviewSaver.LatentPreview',
    settings: [
        {
            id: 'ARS_PreviewSaver.LatentPreview',
            category: ['🎨 ARS Preview Saver', 'Sampling', 'Latent Previews'],
            name: 'Display animated previews when sampling',
            type: 'boolean',
            defaultValue: true,
            onChange(value) {
                if (!value) {
                    //Remove any previewWidgets
                    for (let id of latentPreviewNodes) {
                        let n = app.graph.getNodeById(id)
                        let i = n?.widgets?.findIndex((w) => w.name == 'ars_previewsaver_latentpreview')
                        if (i >= 0) {
                            n.widgets.splice(i,1)[0].onRemove()
                        }
                    }
                    latentPreviewNodes = new Set()
                }
            },
        },
        {
            id: "ARS_PreviewSaver.LatentPreviewRate",
            category: ['🎨 ARS Preview Saver', 'Sampling', 'Latent Preview Rate'],
            name: "Playback rate override.",
            type: 'number',
            attrs: {
                min: 0,
                step: 1,
                max: 60
            },
            tooltip: 'Force a specific frame rate for the playback of latent frames. This should not be confused with the output frame rate and will not match for video models.',
            defaultValue: 0,
        },
    ],
    async setup() {
        let originalGraphToPrompt = app.graphToPrompt
        let graphToPrompt = async function() {
            let res = await originalGraphToPrompt.apply(this, arguments);
            res.workflow.extra['ARS_PreviewSaver_latentpreview'] = app.ui.settings.getSettingValue("ARS_PreviewSaver.LatentPreview")
            res.workflow.extra['ARS_PreviewSaver_latentpreviewrate'] = app.ui.settings.getSettingValue("ARS_PreviewSaver.LatentPreviewRate")
            return res
        }
        app.graphToPrompt = graphToPrompt
    }
})

function getLatentPreviewCtx(id, width, height) {
    const node = getNodeById(id)
    if (!node) {
        return undefined
    }

    let previewWidget = node.widgets.find((w) => w.name == "ars_previewsaver_latentpreview")
    if (!previewWidget) {
        let canvasEl = document.createElement("canvas")
        previewWidget = node.addDOMWidget("ars_previewsaver_latentpreview", "ars_canvas", canvasEl, {
            serialize: false,
            hideOnZoom: false,
        });
        previewWidget.serialize = false
        
        canvasEl.addEventListener('contextmenu', (e)  => {
            e.preventDefault()
            return app.canvas._mousedown_callback(e)
        }, true);
        canvasEl.addEventListener('pointerdown', (e)  => {
            e.preventDefault()
            return app.canvas._mousedown_callback(e)
        }, true);
        canvasEl.addEventListener('mousewheel', (e)  => {
            e.preventDefault()
            return app.canvas._mousewheel_callback(e)
        }, true);
        canvasEl.addEventListener('pointermove', (e)  => {
            e.preventDefault()
            return app.canvas._mousemove_callback(e)
        }, true);
        canvasEl.addEventListener('pointerup', (e)  => {
            e.preventDefault()
            return app.canvas._mouseup_callback(e)
        }, true);

        previewWidget.computeSize = function(width) {
            if (this.aspectRatio) {
                let height = (node.size[0]-20)/ this.aspectRatio + 10;
                if (!(height > 0)) {
                    height = 0;
                }
                this.computedHeight = height + 10;
                return [width, height];
            }
            return [width, -4];//no loaded src, widget should not display
        }
    }
    let canvasEl = previewWidget.element
    if (!previewWidget.ctx || canvasEl.width != width
        || canvasEl.height != height) {
        previewWidget.aspectRatio = width / height
        canvasEl.width = width
        canvasEl.height = height
        
        // Resize node to fit preview
        if (node.computeSize) {
            node.setSize(node.computeSize())
        }
    }
    return canvasEl.getContext("2d")
}

let animateIntervals = {}
function beginLatentPreview(id, previewImages, rate) {
    latentPreviewNodes.add(id)
    if (animateIntervals[id]) {
        clearTimeout(animateIntervals[id])
    }
    let displayIndex = 0
    let node = getNodeById(id)
    //While progress is safely cleared on execution completion.
    //Initial progress must be started here to avoid a race condition
    node.progress = 0
    animateIntervals[id] = setInterval(() => {
        if (getNodeById(id)?.progress == undefined
            || app.canvas.graph.rootGraph != node.graph.rootGraph) {
            clearTimeout(animateIntervals[id])
            delete animateIntervals[id]
            return
        }
        if (!previewImages[displayIndex]) {
            return
        }
        getLatentPreviewCtx(id, previewImages[displayIndex].width,
            previewImages[displayIndex].height)?.drawImage?.(previewImages[displayIndex],0,0)
        displayIndex = (displayIndex + 1) % previewImages.length
    }, 1000/rate);
}

let previewImagesDict = {}
api.addEventListener('ARS_PreviewSaver_latentpreview', ({ detail }) => {
    if (detail.id == null) {
        return
    }
    let previewImages = previewImagesDict[detail.id] = []
    previewImages.length = detail.length

    let idParts = detail.id.split(':')
    for (let i=1; i <= idParts.length; i++) {
        let id = idParts.slice(0,i).join(':')
        beginLatentPreview(id, previewImages, detail.rate)
    }
});

let td = new TextDecoder()
api.addEventListener('b_preview', async (e) => {
    if (Object.keys(animateIntervals).length == 0) {
        return
    }
    e.preventDefault()
    e.stopImmediatePropagation()
    e.stopPropagation()
    const dv = new DataView(await e.detail.slice(0,24).arrayBuffer())
    const index = dv.getUint32(4)
    const idlen = dv.getUint8(8)
    const id = td.decode(dv.buffer.slice(9,9+idlen))
    previewImagesDict[id][index] = await window.createImageBitmap(e.detail.slice(24))
    return false
}, true);
