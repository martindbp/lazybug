<template>
    <div v-if="currRect !== null">
        <div
            class="captiondiv"
            v-if="measureRect === null"
            v-for="index in numBlurLayers"
            :key="index"
            @click.prevent.stop="toggle"
            @dblclick.prevent.stop
            :style="{ opacity: toggleOn ? 1 : 0 }"
        />
        <div
            v-else
            class="captiondiv"
        />
    </div>
</template>

<script>
//
// NOTE: this component is dual purpose: the blur rect and measure rect for devtools
// TODO: refactor this to two separate components sharing some logic
//

const DEFAULT_WIDTH = 916;


function rectsUnion(rects) {
    let r = [Infinity, 0, Infinity, 0];
    for (let rect of rects) {
        if (rect === null) continue;
        const [xMin, xMax, yMin, yMax] = rect;
        r[0] = Math.min(r[0], xMin);
        r[1] = Math.max(r[1], xMax);
        r[2] = Math.min(r[2], yMin);
        r[3] = Math.max(r[3], yMax);
    }
    return r;
}


export default {
    mixins: [mixin],
    props: {
        playerId: { default: null },
        measureRect: { default: null }, // if measure rect set this, otherwise the props below
        prevCaption: { default: null },
        currCaption: { default: null },
        nextCaption: { default: null },
        currTime: { default: null },
        AVElement: { default: null },
        videoFrameSize: { default: null },
        numBlurLayers: { default: 4 },
        blurPadding: { default: 5 },
        blurSidePadding: { default: 20 },
        blurTimeBuffer: { default: 0.15 },
    },
    computed: {
        toggleOn: {
            get: function() { return this.measureRect !== null || this.$store.state.options.blurCaptions; },
            set: function(val) { this.$store.commit('setBlur', val); },
        },
        currRect: function() {
            if (this.measureRect) {
                return this.measureRect;
            }
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
        realAspectRatio: function() {
            if (this.captionData === null) return null;

            const [height, width] = this.captionData['frame_size'];
            return width / height;
        },
        AVElementParentSelector: function() {
            if (!BROWSER_EXTENSION) return null;
            return this.getSiteString('AVElementParentSelector');
        },
    },
    watch: {
        currRect: {
            immediate: true, 
            handler: function() {
                this.updateStyle();
            }
        }
    },
    mounted: function() {
        if (!this.AVElement || !this.AVElement.parentNode) return;
        // Transfer it to the video element
        this.AVElement.parentNode.appendChild(this.$el);
    },
    methods: {
        toggle: function() {
            if (this.measureRect !== null) return;
            this.toggleOn = ! this.toggleOn;
        },
        updateStyle: function() {
            if (this.$el === null ||
                this.$el.children === undefined ||
                this.AVElement === null ||
                this.currRect === null) return;

            let videoRect = this.AVElement.getBoundingClientRect();
            let videoAspectRatio = videoRect.width / videoRect.height;
            let videoParent = this.AVElementParentSelector ? this.AVElement.closest(this.AVElementParentSelector) : null;
            let videoParentRect = videoParent ? videoParent.getBoundingClientRect() : null;
            let parentAspectRatio = videoParent ? videoParentRect.width / videoParentRect.height : null;
            let offsetX = 0;
            let offsetY = 0;
            let subtractX = 0;
            let subtractY = 0;
            let videoWidth = videoRect.width;
            let videoHeight = videoRect.height;
            if (videoParent && parentAspectRatio !== videoAspectRatio) {
                // We're on youtube.com and we have black bars
                offsetX = videoRect.left - videoParentRect.left;
                offsetY = videoRect.top - videoParentRect.top;
            }
            else if (this.measureRect === null && videoAspectRatio !== this.realAspectRatio) {
                // Video is in iframe with different aspect ratio than underlying video
                if (this.realAspectRatio < videoAspectRatio) {
                    // We have black bars on sides
                    videoWidth = this.realAspectRatio * videoRect.height;
                    offsetX = (videoRect.width - videoWidth) / 2; // add the width of the black bar
                    subtractX = 2 * offsetX;
                }
                else {
                    // We have black bars on top/bottom
                    videoHeight = videoRect.width / this.realAspectRatio;
                    offsetY = (videoRect.height - videoHeight) / 2; // add the height of the black bar
                    subtractY = 2 * offsetY;
                }
            }
            let xMin, xMax, yMin, yMax;
            [xMin, xMax, yMin, yMax] = this.currRect;
            if (this.measureRect === null) {
                // Blur more the wider the video element is (for both side padding, normal padding and num blur pixels)
                const blurSidePadding = Math.ceil((videoWidth / DEFAULT_WIDTH) * this.blurSidePadding);
                xMin -= blurSidePadding;
                xMax += blurSidePadding;
            }

            const videoFrameHeight = this.measureRect === null ? this.videoFrameSize[0] : videoHeight;
            const videoFrameWidth = this.measureRect === null ? this.videoFrameSize[1] : videoWidth;
            for (let i = 0; i < this.$el.children.length; i++) {
                const captionDiv = this.$el.children[i];
                const padding = this.measureRect === null ? Math.ceil(1.0 * i * this.blurPadding) : 0; // increase the padding for each div
                const xMinDiv = xMin - padding;
                const yMinDiv = yMin - padding;
                const xMaxDiv = xMax + padding;
                const yMaxDiv = yMax + padding;
                let divWidth = xMaxDiv - xMinDiv;
                let divHeight = yMaxDiv - yMinDiv;
                captionDiv.style.top = offsetY + (videoHeight * yMinDiv / videoFrameHeight) + 'px';
                captionDiv.style.left = offsetX + (videoWidth * xMinDiv / videoFrameWidth) + 'px';
                captionDiv.style.height = ((videoRect.height - subtractY) * divHeight / videoFrameHeight) + 'px';
                captionDiv.style.width = ((videoRect.width - subtractX) * divWidth / videoFrameWidth) + 'px';
                if (this.measureRect === null) {
                    const blurPixels = Math.pow(2, this.numBlurLayers - i - 1);
                    captionDiv.style.backdropFilter = `blur(${blurPixels}px)`;
                }
            }
        },
    }
};
</script>

<style>
.captiondiv {
    position:absolute;
    cursor: pointer;
}
</style>
