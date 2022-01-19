<template>
    <div class="captionmenu">
        <div>
            <SvgButton
                name="move"
                @mousedown.stop.prevent="moveMouseDown"
            />
            <SvgButton @click="$store.commit('increaseCaptionFontScale')" name="math-plus" />
            <SvgButton @click="$store.commit('decreaseCaptionFontScale')" name="math-minus" style="margin-right: 10px" />
            <SvgButton @click="prev" name="play-track-prev" />
            <SvgButton @click="redo" name="redo" />
            <SvgButton @click="slowRedo" name="slow" />
            <SvgButton @click="playPause" :name="paused ? 'play-button' : 'play-pause'" />
            <SvgButton @click="next" name="play-track-next" style="margin-right: 10px" />
            <SvgButton @mousedown="peek(true)" @mouseup="peek(false)" @mouseout="peek(false)" name="eye" style="margin-right: 10px" />
            <SvgButton @click="showOptions" name="options" style="margin-right: 10px" />
            <OptionsDialog />
        </div>
    </div>
</template>

<script>
import SvgButton from './SvgButton.vue'
import OptionsDialog from './OptionsDialog.vue'

export default {
    props: ['prevCaption', 'currCaption', 'nextCaption', 'currTime', 'paused', 'AVElement'],
    components: {
        SvgButton,
        OptionsDialog,
    },
    data: function() { return {
        dragging: false,
        dragStart: null,
        origCaptionOffset: null,
        isPrevMouseOver: false,
    }},
    methods: {
        showOptions: function(event) {
            this.$store.commit('setShowOptions', true);
        },
        moveMouseDown: function(event) {
            this.dragging = true;
            this.dragStart = [event.clientX, event.clientY];
            this.origCaptionOffset = this.captionOffset;
            window.addEventListener("mouseup", this.moveMouseUp);
            window.addEventListener("mousemove", this.mouseMove);
        },
        moveMouseUp: function(event) {
            if (! this.dragging) return;
            event.stopPropagation();
            event.preventDefault();
            this.dragging = false;
            this.dragStart = [null, null];
            this.origCaptionOffset = [null, null];
            window.removeEventListener("mouseup", this.moveMouseUp);
            window.removeEventListener("mousemove", this.mouseMove);
        },
        mouseMove: function(event) {
            if (! this.dragging) return;
            event.stopPropagation();
            event.preventDefault();
            const coords = [
                this.origCaptionOffset[0] + (event.clientX - this.dragStart[0]),
                this.origCaptionOffset[1] + (event.clientY - this.dragStart[1]),
            ];
            this.$store.commit('setCaptionOffset', coords);
        },
        prev: function(event) {
            if (this.prevCaption !== null) {
                this.AVElement.currentTime = this.prevCaption.t0 + 1e-3;
                this.AVElement.play();
                this.$emit('seeked');
            }
        },
        redo: function(event) {
            const goToCaption = this.currCaption !== null ? this.currCaption : this.prevCaption;
            if (goToCaption === null) return;

            this.AVElement.currentTime = goToCaption.t0 + 1e-3;
            this.AVElement.play();
            this.$emit('seeked');
        },
        slowRedo: function() {

        },
        playPause: function(event) {
            if (this.paused) this.AVElement.play();
            else this.AVElement.pause();
        },
        next: function(event) {
            if (this.nextCaption === null) return;
            this.AVElement.currentTime = this.nextCaption.t0 + 1e-3;
            this.AVElement.play();
            this.$emit('seeked');
        },
        peek: function(peeking) {
            this.$store.commit('setPeeking', peeking);
        },
    },
    computed: {
        captionOffset: function() { return this.$store.state.captionOffset; },
    }
};
</script>

<style>
.captionmenu {
    background: black;
    position: absolute;
    top: -30px;
    display: inline-block;
    vertical-align: top;
    font-size: 18px !important;
    opacity: 0;
    transition: opacity 150ms ease-in;
    height: 30px;
}

.captionmenu.show {
    opacity: 1;
    transition-delay: 0ms;
}

.captionmenu .svgbutton {
    top: -4px; /* WHYYYY? */
}
</style>
