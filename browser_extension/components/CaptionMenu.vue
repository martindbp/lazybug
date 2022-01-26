<template>
    <div class="captionmenu">
        <div>
            <SvgButton
                name="move"
                title="Move"
                @mousedown.stop.prevent="moveMouseDown"
            />
            <SvgButton title="Increase font size" @click="$store.commit('increaseCaptionFontScale')" name="math-plus" />
            <SvgButton title="Decrease font size" @click="$store.commit('decreaseCaptionFontScale')" name="math-minus" style="margin-right: 10px" />
            <SvgButton title="Go to previous line" @click="prev" name="play-track-prev" />
            <SvgButton title="Replay this line" @click="redo" name="redo" />
            <SvgButton @click="playPause" :name="paused ? 'play-button' : 'play-pause'" />
            <SvgButton title="Go to next line" @click="next" name="play-track-next" style="margin-right: 10px" />
            <SvgButton title="Peek all" @click="peekAll" name="eye" style="margin-right: 10px" />
            <SvgButton title="Options" @click="showOptions" name="options" />
            <SvgButton title="Dictionary" @click="showDictionary" name="dictionary" />
            <OptionsDialog />
            <DictionaryDialog v-bind:caption="currCaption" />
        </div>
    </div>
</template>

<script>
import SvgButton from './SvgButton.vue'
import OptionsDialog from './OptionsDialog.vue'
import DictionaryDialog from './DictionaryDialog.vue'

export default {
    props: ['prevCaption', 'currCaption', 'nextCaption', 'currTime', 'paused', 'AVElement'],
    components: {
        SvgButton,
        OptionsDialog,
        DictionaryDialog,
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
        showDictionary: function(event) {
            if (this.currCaption && ! this.currCaption.dummy) {
                this.$store.commit('setShowDictionary', true);
            }
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
        peekAll: function() {
            const states = this.$store.state.peekStates;
            states['translation'] = true;
            for (var i = 0; i < states['hz'].length; i++) {
                states['hz'][i] = true;
                states['py'][i] = true;
                states['tr'][i] = true;
            }
            this.$store.commit('setPeekStates', states);
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
