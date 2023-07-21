<template>
    <Caption
        v-if="displayCaption"
        playerId="extension"
        v-bind:captionId="captionId"
        v-bind:AVElement="AVElement"
        v-bind:videoDuration="videoDuration"
        v-bind:videoAPI="videoAPI"
    />
    <VideoPicker v-if="displayCaption" playerId="extension" />
    <DevtoolsDialog v-if="$store.state.extensionOn" />
</template>

<script>
import Caption from './Caption.vue'
import DevtoolsDialog from './DevtoolsDialog.vue'
import VideoPicker from './VideoPicker.vue'

export default {
    mixins: [mixin],
    props: ['playerId'],
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
        this.setObserversAndHandlers();
        $q = this.$q; // global variable in shared.js
    },
    watch: {
        AVElementSelector: function() {
            if (!this.AVElementSelector) return;

            const AVElement = document.querySelector(this.AVElementSelector);
            if (AVElement) {
                this.$store.commit('resetPlayerData', 'extension');
                this.$store.commit('setPlayerData', {playerId: 'extension', AVElement: AVElement, videoDuration: AVElement.duration});
            }
        }
    },
    beforeDestroy: function() {
        if (this.mutationObserver !== null) this.mutationObserver.disconnect();
    },
    methods: {
        getCurrentTime: function() {
            if (! this.AVElement) return 0;
            return this.AVElement.currentTime;
        },
        setCurrentTime: function(t) {
            if (! this.AVElement) return;
            this.AVElement.currentTime = t;
        },
        getDuration: function() {
            if (! this.AVElement) return 0;
            return this.AVElement.duration;
        },
        play: function() {
            if (! this.AVElement) return;
            this.AVElement.play();
        },
        pause: function() {
            if (! this.AVElement) return;
            this.AVElement.pause();
        },
        isPaused: function() {
            if (! this.AVElement) return;
            return this.AVElement.paused;
        },
        setObserversAndHandlers: function() {
            const self = this;

            // Observe position changes of the video element.
            this.mutationObserver = new MutationObserver((mutations) => {
                // If a video element has been added, we update the reference
                if (self.AVElement == null) {
                    for (let mutation of mutations) {
                        for (let node of mutation.addedNodes) {
                            if (node.nodeType !== 1) continue;
                            if (node.matches(self.AVElementSelector)) {
                                self.$store.commit('setPlayerData', {playerId: 'extension', AVElement: node});
                                break;
                            }
                            else if (node.querySelector(self.AVElementSelector)) {
                                self.$store.commit('setPlayerData', {playerId: 'extension', AVElement: node.querySelector(self.AVElementSelector)});
                                break;
                            }
                        }
                        for (let node of mutation.removedNodes) {
                            if (node == self.AVElement) {
                                break;
                            }
                        }
                    }
                }
                else {
                    // in case video changed (ad)
                    self.$store.commit('setPlayerData', {playerId: 'extension', videoDuration: this.AVElement.duration});
                }
            })
            this.mutationObserver.observe(document, {subtree: true, childList: true});

            document.addEventListener('DOMContentLoaded', () => {
                self.$store.commit('setPlayerData', {playerId: 'extension', AVElement: document.querySelector(self.AVElementSelector)});
            });
        },
    },
    computed: {
        AVElementSelector: function() {
            return this.getSiteString('AVElementSelector');
        },
        displayCaption: function() {
            return (
                this.$store.state.extensionOn &&
                this.AVElement &&
                this.captionId &&
                this.$store.state.videoList &&
                this.$store.state.videoList.has(this.captionId)
            );
        },
    },
};
</script>

<style>
</style>
