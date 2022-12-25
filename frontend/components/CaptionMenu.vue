<template>
    <div :class="{ captionmenu: true, docked: ! $store.state.isExtension && $store.state.captionDocked }">
        <SvgButton
            v-if="$store.state.isExtension || ! $store.state.captionDocked"
            name="move"
            title="Move"
            @mousedown.stop.prevent="moveMouseDown"
        />
        <SvgButton v-if="! $store.state.isExtension && $store.state.captionDocked" title="Undock" name="arrowtopleft" @click="clickDock(false)" />
        <SvgButton v-else-if="! $store.state.isExtension" title="Dock" name="dock" @click="clickDock(true)" />
        <SvgButton title="Increase font size" @click="$store.commit('increaseCaptionFontScale')" name="math-plus" />
        <SvgButton title="Decrease font size" @click="$store.commit('decreaseCaptionFontScale')" name="math-minus" style="margin-right: 10px" />
        <SvgButton title="Go to previous line" @click="prev" name="play-track-prev" />
        <SvgButton title="Replay this line" @click="replay" name="replay" />
        <SvgButton @click="playPause" :name="paused ? 'play-button' : 'play-pause'" />
        <SvgButton title="Go to next line" @click="next" name="play-track-next" style="margin-right: 10px" />
        <SvgButton title="Peek all" @click="peekAll" name="eye" style="margin-right: 10px" />
        <SvgButton title="Dictionary" @click="showDictionary" name="dictionary" style="margin-right: 10px"/>
        <SvgButton title="Options" @click="showOptions" name="options" />
        <DictionaryDialog v-bind:caption="data" />
    </div>
</template>

<script>
import SvgButton from './SvgButton.vue'
import DictionaryDialog from './DictionaryDialog.vue'

export default {
    mixins: [mixin],
    props: ['prevCaption', 'currCaption', 'nextCaption', 'data', 'currTime', 'paused', 'videoAPI'],
    components: {
        SvgButton,
        DictionaryDialog,
    },
    data: function() { return {
        dragStart: null,
        origCaptionOffset: null,
        isPrevMouseOver: false,
        keyboardListener: null,
    }},
    mounted: function() {
        const self = this;
        this.keyboardListener = window.addEventListener("keydown", function(event) {
            const shift = event.getModifierState("Shift");
            const ctrl = event.getModifierState("Control");
            const alt = event.getModifierState("Alt");
            if (shift || ctrl || alt) return;

            if (document.activeElement && ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                // Turn off shortcuts when we're focused to an input element
                return;
            }

            if (
                self.$store.state.showOptions ||
                ! self.$store.state.options.keyboardShortcutsToggle ||
                ! self.$store.state.captionData ||
                ! self.$store.state.extensionOn
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
            else if (shortcut === 'pausePlay') {
                self.playPause();
            }
            else if (shortcut === 'next') {
                self.next('keyboard');
            }
            else if (shortcut === 'prev') {
                self.prev('keyboard');
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
        clickDock: function(val) {
            this.$store.commit('setCaptionDocked', val);
        },
        showOptions: function(event) {
            this.$store.commit('setShowDialog', {dialog: 'options', val: true});
        },
        showDictionary: function(event) {
            if (this.data) {
                this.$store.commit('setShowDictionary', {val: true});
            }
        },
        moveMouseDown: function(event) {
            this.$store.commit('setIsMovingCaption', true);
            this.dragStart = [event.clientX, event.clientY];
            this.origCaptionOffset = this.captionOffset;
            window.addEventListener("mouseup", this.moveMouseUp);
            window.addEventListener("mousemove", this.mouseMove);
        },
        moveMouseUp: function(event) {
            if (! this.$store.state.isMovingCaption) return;
            event.stopPropagation();
            event.preventDefault();
            this.$store.commit('setIsMovingCaption', false);
            this.dragStart = [null, null];
            this.origCaptionOffset = [null, null];
            window.removeEventListener("mouseup", this.moveMouseUp);
            window.removeEventListener("mousemove", this.mouseMove);
        },
        mouseMove: function(event) {
            if (! this.$store.state.isMovingCaption) return;
            event.stopPropagation();
            event.preventDefault();
            const coords = [
                this.origCaptionOffset[0] + (event.clientX - this.dragStart[0]),
                this.origCaptionOffset[1] + (event.clientY - this.dragStart[1]),
            ];
            this.$store.commit('setCaptionOffset', coords);
        },
        prev: function(event) {
            if (this.prevCaption === null) return;

            const currentTime = this.videoAPI.getCurrentTime();
            if (event === 'keyboard' && Math.abs(currentTime - this.prevCaption.t0) > 20) {
                this.videoAPI.setCurrentTime(currentTime - 5);
            }
            else {
                this.videoAPI.setCurrentTime(this.prevCaption.t0 + 1e-3);
            }
            this.videoAPI.play();
            this.$emit('seeked');
        },
        replay: function(event) {
            const goToCaption = this.data !== null ? this.data : this.prevCaption;
            if (goToCaption === null) return;

            this.videoAPI.setCurrentTime(goToCaption.t0 + 1e-3);
            this.videoAPI.play();
            this.$emit('seeked');
            this.appendSessionLog([eventsMap['EVENT_REPLAY_CAPTION']]);
        },
        playPause: function(event) {
            if (this.paused) this.videoAPI.play();
            else this.videoAPI.pause();
        },
        next: function(event) {
            if (this.nextCaption === null) return;

            const currentTime = this.videoAPI.getCurrentTime();
            if (event === 'keyboard' && Math.abs(currentTime - this.nextCaption.t0) > 20) {
                this.videoAPI.setCurrentTime(currentTime + 5);
            }
            else {
                this.videoAPI.setCurrentTime(this.nextCaption.t0 + 1e-3);
            }
            this.videoAPI.play();
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
    font-size: 18px !important;
    height: 30px;
    white-space: nowrap;
}

.captionmenu.docked {
    background: rgba(0, 0, 0, 1.0);
    display: block;
}

.captionmenu:not(.docked) {
    position: absolute;
    top: -30px;
    display: inline-block;
    vertical-align: top;
    opacity: 0;
    transition: opacity 150ms ease-in;
    transition: background-color 300ms linear;
}

.captionmenu:not(.docked).show {
    opacity: 1;
    transition-delay: 0ms;
}

#extroot .captionmenu .svgbutton {
    top: -5px; /* WHYYYY? */
}
</style>
