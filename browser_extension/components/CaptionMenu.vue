<template>
    <div class="captionmenu">
        <SvgButton
            name="move"
            title="Move"
            @mousedown.stop.prevent="moveMouseDown"
        />
        <SvgButton title="Increase font size" @click="$store.commit('increaseCaptionFontScale')" name="math-plus" />
        <SvgButton title="Decrease font size" @click="$store.commit('decreaseCaptionFontScale')" name="math-minus" style="margin-right: 10px" />
        <SvgButton title="Go to previous line" @click="prev" name="play-track-prev" />
        <SvgButton title="Replay this line" @click="replay" name="replay" />
        <SvgButton @click="playPause" :name="paused ? 'play-button' : 'play-pause'" />
        <SvgButton title="Go to next line" @click="next" name="play-track-next" style="margin-right: 10px" />
        <SvgButton title="Peek all" @click="peekAll" name="eye" style="margin-right: 10px" />
        <SvgButton title="Dictionary" @click="showDictionary" name="dictionary" style="margin-right: 10px"/>
        <SvgButton title="Options" @click="showOptions" name="options" />
        <OptionsDialog />
        <DictionaryDialog v-bind:caption="data" />
    </div>
</template>

<script>
import SvgButton from './SvgButton.vue'
import OptionsDialog from './OptionsDialog.vue'
import DictionaryDialog from './DictionaryDialog.vue'

export default {
    mixins: [mixin],
    props: ['prevCaption', 'currCaption', 'nextCaption', 'data', 'currTime', 'paused', 'AVElement'],
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
        keyboardListener: null,
    }},
    mounted: function() {
        const self = this;
        this.keyboardListener = window.addEventListener("keydown", function(event) {
            if (document.activeElement && ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                // Turn off shortcuts when we're focused to an input element
                return;
            }

            if (
                self.$store.state.showOptions ||
                ! self.$store.state.options.keyboardShortcutsToggle ||
                ! self.$store.state.captionData ||
                ! self.$store.state.options.extensionToggle
            ) {
                return;
            }

            let shortcut = null;
            for (const [key, val] of Object.entries(self.$store.state.options.keyboardShortcuts)) {
                if (event.code === val) {
                    shortcut = key;
                    break;
                }
            }
            if (shortcut === null) {
                return;
            }

            event.preventDefault();
            event.stopPropagation();
            if (shortcut === 'peek') {
                self.peekAll();
            }
            else if (shortcut === 'next') {
                self.next();
            }
            else if (shortcut === 'prev') {
                self.prev();
            }
            else if (shortcut === 'replay') {
                self.replay();
            }
            else if (shortcut === 'dictionary') {
                self.showDictionary();
            }
            else if (shortcut === 'peekFullTr') {
                self.$store.commit('setPeekState', {type: 'translation'});
            }
            else if (shortcut === 'peekPy') {
                self.$store.commit('setPeekState', {type: 'py'});
            }
            else if (shortcut === 'peekHz') {
                self.$store.commit('setPeekState', {type: 'hz'});
            }
            else if (shortcut === 'peekTr') {
                self.$store.commit('setPeekState', {type: 'tr'});
            }
        }, {capture: true});
    },
    beforeDestroy: function() {
        window.removeEventListener('keydown', this.keyboardListener);
    },
    methods: {
        showOptions: function(event) {
            this.$store.commit('setShowOptions', true);
        },
        showDictionary: function(event) {
            if (this.data && ! this.data.dummy) {
                this.$store.commit('setShowDictionary', {val: true});
            }
        },
        moveMouseDown: function(event) {
            this.dragging = true;
            this.dragStart = [event.clientX, event.clientY];
            this.origCaptionOffset = this.captionOffset;
            this.$store.commit('setIsMovingCaption', true);
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
            this.$store.commit('setIsMovingCaption', false);
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
        replay: function(event) {
            const goToCaption = this.data !== null ? this.data : this.prevCaption;
            if (goToCaption === null) return;

            this.AVElement.currentTime = goToCaption.t0 + 1e-3;
            this.AVElement.play();
            this.$emit('seeked');
            this.appendSessionLog([eventsMap['EVENT_REPLAY_CAPTION']]);
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
            this.appendSessionLog([eventsMap['EVENT_PEEK_ALL']]);
        },
    },
    computed: {
        captionOffset: function() { return this.$store.state.captionOffset; },
    }
};
</script>

<style>
.captionmenu {
    background: rgba(0, 0, 0, 0.75);
    transition: background-color 300ms linear;
    position: absolute;
    top: -30px;
    display: inline-block;
    vertical-align: top;
    font-size: 18px !important;
    opacity: 0;
    transition: opacity 150ms ease-in;
    height: 30px;
    white-space: nowrap;
}

.captionmenu.show {
    opacity: 1;
    transition-delay: 0ms;
}

.captionmenu .svgbutton {
    top: -5px; /* WHYYYY? */
}
</style>
