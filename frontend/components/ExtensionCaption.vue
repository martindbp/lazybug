<template>
    <Caption
        v-if="displayCaption"
        v-bind:captionId="$store.state.captionId"
        v-bind:AVElement="$store.state.AVElement"
        v-bind:videoDuration="$store.state.videoDuration"
        v-bind:videoAPI="videoAPI"
    />
    <VideoPicker />
    <DevtoolsDialog />
</template>

<script>
import Caption from './Caption.vue'
import DevtoolsDialog from './DevtoolsDialog.vue'
import VideoPicker from './VideoPicker.vue'

export default {
    mixins: [mixin],
    components: {
        Caption,
        DevtoolsDialog,
        VideoPicker,
    },
    data: function() {
        return {
            mutationObserver: null,
            videoAPI: {
                getCurrentTime: this.getCurrentTime,
                setCurrentTime: this.setCurrentTime,
                getDuration: this.getDuration,
                play: this.play,
                pause: this.pause,
                isPaused: this.isPaused,
            },
        };
    },
    mounted: function(){
        const AVElement = document.querySelector(this.AVElementSelector);
        if (AVElement) {
            this.$store.commit('setAVElement', AVElement);
            this.$store.commit('setVideoDuration', AVElement.duration);
        }
        this.setObserversAndHandlers();
    },
    beforeDestroy: function() {
        if (this.mutationObserver !== null) this.mutationObserver.disconnect();
    },
    methods: {
        getCurrentTime: function() {
            if (! this.$store.state.AVElement) return 0;
            return this.$store.state.AVElement.currentTime;
        },
        setCurrentTime: function(t) {
            if (! this.$store.state.AVElement) return;
            this.$store.state.AVElement.currentTime = t;
        },
        getDuration: function() {
            if (! this.$store.state.AVElement) return 0;
            return this.$store.state.AVElement.duration;
        },
        play: function() {
            if (! this.$store.state.AVElement) return;
            this.$store.state.AVElement.play();
        },
        pause: function() {
            if (! this.$store.state.AVElement) return;
            this.$store.state.AVElement.pause();
        },
        isPaused: function() {
            if (! this.$store.state.AVElement) return;
            return this.$store.state.AVElement.paused;
        },
        setObserversAndHandlers: function() {
            const self = this;

            // Observe position changes of the video element.
            this.mutationObserver = new MutationObserver((mutations) => {
                // If a video element has been added, we update the reference
                if (self.$store.state.AVElement == null) {
                    for (let mutation of mutations) {
                        for (let node of mutation.addedNodes) {
                            if (node.nodeType !== 1) continue;
                            if (node.matches(self.AVElementSelector)) {
                                self.$store.commit('setAVElement', node);
                                break;
                            }
                            else if (node.querySelector(self.AVElementSelector)) {
                                self.$store.commit('setAVElement', node.querySelector(self.AVElementSelector));
                                break;
                            }
                        }
                        for (let node of mutation.removedNodes) {
                            if (node == self.$store.state.AVElement) {
                                break;
                            }
                        }
                    }
                }
                else {
                    // in case video changed (ad)
                    self.$store.commit('setVideoDuration', this.$store.state.AVElement.duration);
                }
            })
            this.mutationObserver.observe(document, {subtree: true, childList: true});

            document.addEventListener('DOMContentLoaded', () => {
                self.$store.commit('setAVElement', document.querySelector(self.AVElementSelector));
            });
        },
    },
    computed: {
        AVElementSelector: function() {
            return this.getSiteString('AVElementSelector');
        },
        displayCaption: function() {
            return (
                this.$store.state.AVElement &&
                this.$store.state.extensionOn &&
                this.$store.state.captionId &&
                this.$store.state.videoList &&
                this.$store.state.videoList.has(this.$store.state.captionId)
            );
        },
    },
};
</script>

<style>
</style>
