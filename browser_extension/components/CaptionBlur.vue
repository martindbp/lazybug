<template>
    <div v-if="currRect !== null">
        <div
            class="blurdiv"
            v-for="index in numBlurLayers"
            :key="index"
            @click.prevent.stop="toggle"
            @dblclick.prevent.stop
            :style="{ opacity: toggleOn ? 1 : 0 }"
        />
    </div>
</template>

<script>
const DEFAULT_WIDTH = 916;


function rectsUnion(rects) {
    let r = [Infinity, 0, Infinity, 0];
    for (let rect of rects) {
        const [xMin, xMax, yMin, yMax] = rect;
        r[0] = Math.min(r[0], xMin);
        r[1] = Math.max(r[1], xMax);
        r[2] = Math.min(r[2], yMin);
        r[3] = Math.max(r[3], yMax);
    }
    return r;
}


export default {
    props: {
        prevCaption: { default: null },
        currCaption: { default: null },
        nextCaption: { default: null },
        currTime: { default: null },
        AVElement: { default: null },
        videoFrameSize: { default: null },
        videoCaptionTopPx: { default: null },
        numBlurLayers: { default: 4 },
        blurPadding: { default: 5 },
        blurSidePadding: { default: 20 },
        blurTimeBuffer: { default: 0.15 },
    },
    data: function() { return {
        toggleOn: true,
    }},
    computed: {
        currRect: function() {
            let rects = this.currCaption !== null ? this.currCaption.boundingRects : [];
            if (this.prevCaption !== null) {
                if (this.currTime < this.prevCaption.t1 + this.blurTimeBuffer) {
                    rects = rects.concat(this.prevCaption.boundingRects);
                }
            }
            if (this.nextCaption !== null) {
                if (this.currTime > this.nextCaption.t0 - this.blurTimeBuffer) {
                    rects = rects.concat(this.nextCaption.boundingRects);
                }
            }
            if (rects.length === 0) return null;
            return rectsUnion(rects);
        },
    },
    watch: {
        currRect: {
            immediate: true, 
            handler: function() {
                this.updateBlurStyle();
            }
        }
    },
    mounted: function() {
        if (this.AVElement === null) return;
        // Transfer it to the video element
        this.AVElement.parentNode.appendChild(this.$el);
    },
    methods: {
        toggle: function() {
            this.toggleOn = ! this.toggleOn;
        },
        updateBlurStyle: function() {
            if (this.$el === null ||
                this.$el.children === undefined ||
                this.AVElement === null ||
                this.currRect === null) return;

            var videoRect = this.AVElement.getBoundingClientRect();
            var videoParentRect = this.AVElement.parentNode.getBoundingClientRect();
            let xMin, xMax, yMin, yMax;
            [xMin, xMax, yMin, yMax] = this.currRect;
            // Blur more the wider the video element is (for both side padding, normal padding and num blur pixels)
            const blurSidePadding = Math.ceil((videoRect.width / DEFAULT_WIDTH) * this.blurSidePadding);
            xMin -= blurSidePadding;
            xMax += blurSidePadding;
            yMin += this.videoCaptionTopPx;
            yMax += this.videoCaptionTopPx;
            for (var i = 0; i < this.$el.children.length; i++) {
                const blurDiv = this.$el.children[i];
                const padding = Math.ceil((videoRect.width / DEFAULT_WIDTH) * i * this.blurPadding); // increase the padding for each div
                const xMinDiv = xMin - padding;
                const yMinDiv = yMin - padding;
                const xMaxDiv = xMax + padding;
                const yMaxDiv = yMax + padding;
                let divWidth = xMaxDiv - xMinDiv;
                let divHeight = yMaxDiv - yMinDiv;
                let parentOffset = videoRect.left - videoParentRect.left;
                blurDiv.style.top = (videoRect.height * yMinDiv / this.videoFrameSize[0]) + 'px';
                blurDiv.style.left = parentOffset + (videoRect.width * xMinDiv / this.videoFrameSize[1]) + 'px';
                blurDiv.style.height = (videoRect.height * divHeight / this.videoFrameSize[0]) + 'px';
                blurDiv.style.width = (videoRect.width * divWidth / this.videoFrameSize[1]) + 'px';
                const blurPixels = Math.ceil((videoRect.width / DEFAULT_WIDTH) * (this.numBlurLayers - i));
                blurDiv.style.backdropFilter = `blur(${blurPixels}px)`;
            }
        },
    }
};
</script>

<style>
.blurdiv {
    position:absolute;
    cursor: pointer;
}
</style>
