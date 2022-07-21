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
    props: {
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
            get: function() { return this.$store.state.options.blurCaptions; },
            set: function(val) { this.$store.commit('setBlur', val); },
        },
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
        realAspectRatio: function() {
            if (this.$store.state.captionData === null) return null;

            const [height, width] = this.$store.state.captionData['frame_size'];
            return width / height;
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

            let videoRect = this.AVElement.getBoundingClientRect();
            let videoAspectRatio = videoRect.width / videoRect.height;
            let videoParent = this.AVElement.closest('.html5-video-player')
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
            else if (videoAspectRatio !== this.realAspectRatio) {
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
            // Blur more the wider the video element is (for both side padding, normal padding and num blur pixels)
            const blurSidePadding = Math.ceil((videoWidth / DEFAULT_WIDTH) * this.blurSidePadding);
            xMin -= blurSidePadding;
            xMax += blurSidePadding;
            for (let i = 0; i < this.$el.children.length; i++) {
                const blurDiv = this.$el.children[i];
                const padding = Math.ceil(1.0 * i * this.blurPadding); // increase the padding for each div
                const xMinDiv = xMin - padding;
                const yMinDiv = yMin - padding;
                const xMaxDiv = xMax + padding;
                const yMaxDiv = yMax + padding;
                let divWidth = xMaxDiv - xMinDiv;
                let divHeight = yMaxDiv - yMinDiv;
                blurDiv.style.top = offsetY + (videoHeight * yMinDiv / this.videoFrameSize[0]) + 'px';
                blurDiv.style.left = offsetX + (videoWidth * xMinDiv / this.videoFrameSize[1]) + 'px';
                blurDiv.style.height = ((videoRect.height - subtractY) * divHeight / this.videoFrameSize[0]) + 'px';
                blurDiv.style.width = ((videoRect.width - subtractX) * divWidth / this.videoFrameSize[1]) + 'px';
                const blurPixels = Math.pow(2, this.numBlurLayers - i - 1);
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
