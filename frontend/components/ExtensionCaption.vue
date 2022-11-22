<template>
    <Caption
        v-if="captionId && AVElement && $store.state.extensionOn"
        v-bind:captionId="captionId"
        v-bind:AVElement="AVElement"
        v-bind:videoDuration="$store.state.videoDuration"
        v-bind:videoAPI="videoAPI"
    />
    <DevtoolsDialog />
</template>

<script>
import Caption from './Caption.vue'
import DevtoolsDialog from './DevtoolsDialog.vue'

export default {
    mixins: [mixin],
    components: {
        Caption,
        DevtoolsDialog,
    },
    data: function() {
        return {
            AVElement: null,
            url: window.location.href,
            localVideoHash: null,
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
        this.AVElement = document.querySelector(this.AVElementSelector);
        if (this.AVElement) {
            this.$store.commit('setVideoDuration', this.AVElement.duration);
        }
        this.setObserversAndHandlers();
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
            window.addEventListener('lazybugviewlocal', function(event) {
                self.localVideoHash = event.detail;
            });

            // Observe position changes of the url / video element.
            this.mutationObserver = new MutationObserver((mutations) => {
                // The URL and video may change without reloading page, e.g. Youtube is an SPA
                if (window.location.href !== self.url) {  // may help with performance to check before assigning?
                    self.url = window.location.href;
                }

                // If a video element has been added, we update the reference
                if (self.AVElement == null) {
                    for (let mutation of mutations) {
                        for (let node of mutation.addedNodes) {
                            if (node.nodeType !== 1) continue;
                            if (node.matches(self.AVElementSelector)) {
                                self.AVElement = node;
                                break;
                            }
                            else if (node.querySelector(self.AVElementSelector)) {
                                self.AVElement = node.querySelector(self.AVElementSelector);
                                console.log('setting AVElement to', self.AVElement)
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
                    self.$store.commit('setVideoDuration', this.AVElement.duration);
                }
            })
            this.mutationObserver.observe(document, {subtree: true, childList: true});

            document.addEventListener('DOMContentLoaded', () => {
                self.AVElement = document.querySelector(self.AVElementSelector);
            });
        },
    },
    watch: {
        videoId: {
            immediate: true,
            handler: function() {
                this.$store.commit('setVideoId', this.videoId);
            }
        },
    },
    computed: {
        AVElementSelector: function() {
            return this.getSiteString('AVElementSelector');
        },
        videoId: function() {
            if (this.url !== null) {
                const id = extractCurrentVideoId(this.$store.state.STRINGS, this.url); // eslint-disable-line
                return id;
            }
            return null;
        },
        captionId: function() {
            let captionId = null;
            if (this.localVideoHash !== null) {
                captionId = 'local-' + this.localVideoHash;
            }

            if (this.videoId !== null) {
                captionId = getCurrentSite() + '-' + this.videoId;
            }

            if (this.$store.state.videoList === null || ! this.$store.state.videoList.has(captionId)) {
                return null;
            }

            console.log('Setting captionId to', captionId);
            return captionId;
        },
    },
};
</script>

<style>
</style>
