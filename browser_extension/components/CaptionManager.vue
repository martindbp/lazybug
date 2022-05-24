<template>
    <div v-if="captionId && AVElement && $store.state.options.extensionToggle">
        <CaptionContainer
            id="captionroot"
            ref="captionroot"
            :style="{ fontSize: captionFontSize+'px' }"
            v-bind:isLoading="isLoading"
            v-bind:isLikelyAnAd="isLikelyAnAd"
            v-bind:translationType="translationType"
            v-bind:currentCaptionIdx="currentCaptionIdx"
            v-bind:firstCaption="firstCaption"
            v-bind:prevCaption="prevCaption"
            v-bind:currCaption="currCaption"
            v-bind:nextCaption="nextCaption"
            v-bind:currTime="currTime"
            v-bind:paused="paused"
            v-bind:AVElement="AVElement"
            v-bind:pauseDuration="pauseDuration"
            v-on:seeked="seekedFromMenu = true"
            v-on:mouseOver="pauseDuration = null"
        />
        <CaptionBlur
            id="blurroot"
            ref="blurroot"
            v-if="$store.state.captionData !== null && $store.state.options.extensionToggle"
            v-bind:prevCaption="prevCaption"
            v-bind:currCaption="currCaption"
            v-bind:nextCaption="nextCaption"
            v-bind:currTime="currTime"
            v-bind:AVElement="AVElement"
            v-bind:videoFrameSize="videoFrameSize"
        />
    </div>
</template>

<script>
import CaptionContainer from './CaptionContainer.vue'
import CaptionBlur from './CaptionBlur.vue'

const DEFAULT_FONT_SIZE = 24;
const DEFAULT_WIDTH = 916;
const CAPTION_END_BUFFER_TIME = 1;

let lastCaptionIdxGlobal = 0;

export default {
    mixins: [mixin],
    components: {CaptionContainer, CaptionBlur},
    data: function() {
        return {
            AVElementSelector: '#primary video, #player-theater-container video',
            url: window.location.href,
            localVideoHash: null,
            currTime: -1000.5,
            AVElement: null,
            videoDuration: null, // keep track of changes to it (could be ads)
            resizeObserver: null,
            mutationObserver: null,
            paused: null,
            lastPausedAt: null,
            automaticallyPausedThisCaption: false,
            minHeight: null,
            captionFontSize: null,
            seeked: false,
            prevCaption: null,
            currCaption: null,
            nextCaption: null,
            translationType: null, // human vs. machine
            pauseDuration: null,
            keyboardListener: null,
        };
    },
    mounted: function(){
        this.setUpdateInterval();
        this.AVElement = document.querySelector(this.AVElementSelector);
        if (this.AVElement) {
            this.videoDuration = this.AVElement.duration;
        }
        this.setObserversAndHandlers();
    },
    beforeDestroy: function() {
        clearInterval(this.currentTimeInterval);
        window.removeEventListener('load', this.updateCaptionPositionBlurFontSize);
        window.removeEventListener('keydown', this.keyboardListener);
        document.removeEventListener('fullscreenchange', this.fullscreenChangeListener);
        if (this.mutationObserver !== null) this.mutationObserver.disconnect();
        if (this.resizeObserver !== null) this.resizeObserver.disconnect();
    },
    beforeUpdate: function() {
        if ([null, undefined].includes(this.$refs.captionroot) || [null, undefined].includes(this.$refs.captionroot.$el)) return;

        let currMinHeight = this.$refs.captionroot.$el.style.minHeight;
        if (currMinHeight === '') currMinHeight = 0;
        else {
            currMinHeight = parseInt(currMinHeight); // NOTE: works for e.g. '10px', the 'px' is ignored
        }
        if (this.currCaption === null && this.minHeight === null) {
            // Since we're changing to an empty caption from a non-empty one, we transfer the min height to the empty one,
            // so it doesn't collapse
            var rect = this.$refs.captionroot.$el.getBoundingClientRect();
            this.minHeight = rect.height;
        }
    },
    updated: function() {
        // New text may have changed the size of the caption, so need to update the position
        const self = this;
        this.$nextTick(function () {
            self.updateCaptionPositionBlurFontSize();
            if (! [null, undefined].includes(self.$refs.captionroot) && ! [null, undefined].includes(self.$refs.captionroot.$el)) {
                self.$refs.captionroot.$el.style.minHeight = self.minHeight === null ? '0px' : self.minHeight + 'px';

                // Make sure the root is always as wide as the menu
                const menuWidth = self.$refs.captionroot.$refs.menu.$el.getBoundingClientRect().width;
                self.$refs.captionroot.$el.style.minWidth = menuWidth + 'px';
            }
        });
    },
    watch: {
        AVElement: {
            immediate: true, 
            handler: function(newValue) {
                const self = this;

                // When the AVElement updates, we need to update `paused` and the event handlers for playing/pausing/resizing
                if (this.resizeObserver !== null) {
                    this.resizeObserver.disconnect();
                    this.resizeObserver = null;
                }

                if (! newValue) return;

                this.paused = newValue ? newValue.paused : false;
                newValue.addEventListener('pause', () => {
                    self.paused = true;
                });
                newValue.addEventListener('play', () => {
                    self.paused = false;
                });
                newValue.addEventListener('seeked', this.onSeeked);

                this.resizeObserver = new ResizeObserver(this.updateCaptionPositionBlurFontSize)
                this.resizeObserver.observe(newValue);
            }
        },
        captionId: {
            immediate: true,
            handler: function() {
                this.$store.commit('setCaptionId', this.captionId);
                this.fetchCaptionMaybe();
            }
        },
        videoId: {
            immediate: true,
            handler: function() {
                this.$store.commit('setVideoId', this.videoId);
            }
        },
        '$store.state.videoList': {
            immediate: true,
            handler: function() {
                this.fetchCaptionMaybe();
            }
        },
        captionOffset: function() {
            this.updateCaptionPositionBlurFontSize();
        },
        captionFontScale: function() {
            this.updateCaptionPositionBlurFontSize();
        },
        currentCaptionIdx: function(newIdx, oldIdx) {
            if (newIdx === oldIdx) return;

            const captionData = this.$store.state.captionData;

            if (captionData === null || this.currentCaptionIdx === null) {
                this.prevCaption = null;
            }
            else if (Array.isArray(this.currentCaptionIdx)) {
                const prevIdx = this.currentCaptionIdx[0];
                if (prevIdx !== null) {
                    this.prevCaption = captionArrayToDict(captionData.lines[prevIdx], captionData);
                }
            }
            else if (this.currentCaptionIdx > 0) {
                this.prevCaption = captionArrayToDict(captionData.lines[this.currentCaptionIdx - 1], captionData);
            }
            else {
                this.prevCaption = null;
            }

            if (captionData === null || this.currentCaptionIdx === null || Array.isArray(this.currentCaptionIdx)) {
                if (this.currCaption !== null) {
                    this.currCaption = null;
                    this.minHeight = null;  // when the caption changes we reset any min height set
                }
            }
            else {
                this.currCaption = captionArrayToDict(captionData.lines[this.currentCaptionIdx], captionData);
                this.minHeight = null;  // when the caption changes we reset any min height set
                this.automaticallyPausedThisCaption = false;
                const dt = Date.now() - this.$store.state.sessionTime;
                this.appendSessionLog([eventsMap['EVENT_SHOW_CAPTION_IDX'], this.currentCaptionIdx, dt]);
            }

            if (captionData === null || this.currentCaptionIdx === null) {
                this.nextCaption = null;
            }
            else if (Array.isArray(this.currentCaptionIdx)) {
                const nextIdx = this.currentCaptionIdx[1];
                if (nextIdx !== null) {
                    this.nextCaption = captionArrayToDict(captionData.lines[nextIdx], captionData);
                }
            }
            else if (this.currentCaptionIdx < captionData.lines.length - 1) {
                this.nextCaption = captionArrayToDict(captionData.lines[this.currentCaptionIdx + 1], captionData);
            }
            else {
                this.nextCaption = null;
            }
        },
    },
    methods: {
        fetchCaptionMaybe: function() {
            if (this.captionId === null || [null, undefined].includes(chrome.runtime)) {
                this.$store.commit('setCaptionDataAndHash', {data: null, hash: null});
                return;
            }
            if (this.$store.state.captionHash === 'fetching') return;

            this.$store.commit('resetResourceFetchError', 'caption data');
            this.$store.commit('setCaptionDataAndHash', {data: null, hash: 'fetching'});

            const self = this;
            chrome.runtime.sendMessage({'type': 'getCaptions', 'data': {
                'captionId': self.captionId,
            }}, function onResponse(message) {
                if (message === 'error') {
                    self.$store.commit('setResourceFetchError', 'caption data');
                    self.$store.commit('setCaptionDataAndHash', {data: null, hash: null});
                    return false;
                }
                self.$store.commit('resetResourceFetchError', 'caption data');
                if (self.$store.state.captionHash === message.hash) return true;

                console.log(message);
                self.$store.commit('setCaptionDataAndHash', message);
                // Append the initial pinned peek values
                for (const type of ['py', 'hz', 'tr', 'translation']) {
                    if (self.$store.state.options.pin[type] === true) {
                        self.appendSessionLog([getEvent('pin_row', type), true]);
                    }
                }
                self.appendSessionLog([eventsMap['EVENT_BLUR'], self.$store.state.options.blurCaptions]);
                return true;
            });
        },
        onSeeked: function() {
            this.seeked = true;
            if (this.seekedFromMenu) {
                // If we seeked from menu (back/next/redo) then we want to automatically pause after
                this.automaticallyPausedThisCaption = false;
            }
            else {
                // Set this to true in case we seeked into the middle (or end) of a caption, then we don't want to pause
                // at the end
                this.automaticallyPausedThisCaption = true;
            }
            this.seekedFromMenu = false;
            this.pauseDuration = null;
        },
        setObserversAndHandlers: function() {
            const self = this;
            window.addEventListener('load', this.updateCaptionPositionBlurFontSize);
            window.addEventListener('zimuviewlocal', function(event) {
                self.localVideoHash = event.detail;
            });
            document.addEventListener('fullscreenchange', this.fullscreenChangeListener);

            // Update the caption position on any changes to the page (except to the caption itself), since there is no way to
            // observe position changes of the video element.
            this.mutationObserver = new MutationObserver((mutations) => {
                let update = false;
                for(let mutation of mutations) {
                    for(let node of mutation.addedNodes) {
                        if (! (node.classList && node.classList.contains('caption'))) {
                            update = true;
                            break;
                        }
                    }
                    if (update) break;
                }
                if (update) {
                    self.updateCaptionPositionBlurFontSize();
                }

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
                    self.videoDuration = self.AVElement.duration; // in case video changed (ad)
                }
            })
            this.mutationObserver.observe(document, {subtree: true, childList: true});

            document.addEventListener('DOMContentLoaded', () => {
                self.AVElement = document.querySelector(self.AVElementSelector);
            });

            this.keyboardListener = window.addEventListener("keydown", function(event) {
                if (self.pauseDuration !== null) {
                    self.pauseDuration = null; // cancel auto pausing for any key down
                    // Make sure it doesn't continue to regular keyboard shortcuts
                    event.preventDefault();
                    event.stopPropagation();
                }
            });
        },
        fullscreenChangeListener: function() {
            // If we go full screen and caption component is outside div element, it would not be visible, so reset position
            this.$store.commit('setCaptionOffset', [0, 0]);
            this.updateCaptionPositionBlurFontSize();
        },
        setUpdateInterval: function() {
            const self = this;
            self.currentTimeInterval = setInterval(() => {
                if (self.AVElement === null || self.$store.state.captionData == null) return;
                const newTime = self.AVElement.currentTime;
                if (self.paused && self.automaticallyPausedThisCaption && ! self.seeked && ! self.seekedFromMenu) {
                    return;
                }

                const isNextCaption = (
                    self.nextCaption !== null &&
                    newTime >= self.nextCaption.t0 &&
                    newTime <= self.nextCaption.t1
                );
                let wordsPerSecond = 0;
                if (isNextCaption && (self.currCaption || self.prevCaption)) {
                    const c = self.currCaption || self.prevCaption;
                    wordsPerSecond = c.alignments.length / (newTime - c.t0);
                }

                const canPause = (
                    isNextCaption &&
                    ! self.automaticallyPausedThisCaption &&
                    ! self.paused &&
                    ! self.seeked &&
                    ! self.seekedFromMenu
                );

                if (self.options.autoPause === 'basic' && canPause) {
                    self.automaticallyPausedThisCaption = true;
                    self.AVElement.pause();
                }
                else if (self.options.autoPause === 'WPS' && canPause && wordsPerSecond > self.options.WPSThreshold) {
                    self.automaticallyPausedThisCaption = true;
                    self.AVElement.pause();
                    const c = self.currCaption || self.prevCaption;
                    self.pauseDuration = c.alignments.length / self.options.WPSThreshold - (newTime - c.t0);
                    console.log('PAUSING FOR', self.pauseDuration);
                    setTimeout(function() {
                        if (self.pauseDuration !== null) {
                            self.AVElement.play(); // resume
                            self.pauseDuration = null;
                        }
                    }, self.pauseDuration * 1000);
                }
                else {
                    self.currTime = newTime;
                }
                self.seeked = false;
            }, 10);
        },
        updateCaptionPositionBlurFontSize: function() {
            if (this.AVElement === null || [null, undefined].includes(this.$refs.captionroot)) return;
            var videoRect = this.AVElement.getBoundingClientRect();
            // var captionRect = this.$refs.captionroot.$el.getBoundingClientRect();
            this.$refs.captionroot.$el.style.left = ((videoRect.left+window.scrollX) + 0.1 * videoRect.width + this.captionOffset[0]) + 'px';
            this.$refs.captionroot.$el.style.top = (0.8 * (videoRect.bottom+window.scrollY) + this.captionOffset[1]) + 'px';
            if (this.$refs.blurroot) {
                this.$refs.blurroot.updateBlurStyle();
            }

            // We scale the font size with the width of the video element and the font scale selected by the user.
            // At width=DEFAULT_WIDTH and fontScale=0.5 we want fontSize=DEFAULT_FONT_SIZE
            //this.captionFontSize = Math.round(2 * DEFAULT_FONT_SIZE * this.captionFontScale * (this.AVElement.getBoundingClientRect().width / DEFAULT_WIDTH));

            // Actually, scaling is not working well, let's just keep it constant
            this.captionFontSize = Math.round(2 * DEFAULT_FONT_SIZE * this.captionFontScale);
        },
        getCurrentCaptionIdx: function(withTimingOffset) {
            const captionData = this.$store.state.captionData;
            if (captionData === null) return null;

            const lines = captionData.lines
            const lastSeenCaption = captionArrayToDict(lines[lastCaptionIdxGlobal], captionData);
            const lastSeenCaptionT0 = lastSeenCaption.t0 + (withTimingOffset ? lastSeenCaption.timingOffset : 0);
            if (this.currTime < lastSeenCaptionT0) {
                // Start over search from the beginning
                lastCaptionIdxGlobal = 0;
            }

            for (var i = lastCaptionIdxGlobal; i < lines.length; i++) {
                let caption = captionArrayToDict(lines[i], captionData);
                let captionT0 = caption.t0 + (withTimingOffset ? caption.timingOffset : 0)
                let prevCaption = i > 0 ? captionArrayToDict(lines[i-1], captionData) : null;
                if (this.currTime >= captionT0 && this.currTime <= caption.t1) {
                    lastCaptionIdxGlobal = i;
                    return i;
                }
                else if (prevCaption && this.currTime > prevCaption.t1 && this.currTime < captionT0) {
                    // In between two lines
                    lastCaptionIdxGlobal = i-1;

                    // If we're still close to the prevCaption, we keep it
                    if (this.currTime < Math.min(prevCaption.t1 + CAPTION_END_BUFFER_TIME, captionT0)) {
                        return i-1;
                    }
                    return [i-1, i];
                }
            }

            const firstCaption = captionArrayToDict(lines[0], captionData)
            const lastCaption = captionArrayToDict(lines[lines.length - 1], captionData)
            const firstCaptionT0 = firstCaption.t0 + (withTimingOffset ? firstCaption.timingOffset : 0);
            const lastCaptionT1 = lastCaption.t1 + (withTimingOffset ? lastCaption.timingOffset : 0);
            if (this.currTime < firstCaptionT0) {
                return [null, 0];
            }
            else if (this.currTime > lastCaptionT1) {
                return [lines.length-1, null];
            }
            return null;
        },
    },
    computed: {
        isLikelyAnAd: function() {
            if (this.videoDuration === NaN || this.$store.state.captionData === null) return false;

            const captionDuration = this.$store.state.captionData.video_length;
            const isAd = Math.abs(this.videoDuration - captionDuration) > 0.5;
            console.log('Is ad:', isAd);
            return isAd;
        },
        firstCaption: function() {
            const data = this.$store.state.captionData;
            if (data !== null && data.lines.length > 0) {
                return captionArrayToDict(data.lines[0], this.$store.state.captionData);
            }
        },
        translationType: function() {
            if (this.firstCaption) {
                return this.firstCaption.translations.length > 2 ? 'human' : 'machine';
            }
        },
        isLoading: function() {
            return (
                this.captionId !== null && (
                    this.$store.state.videoList === null ||
                    this.$store.state.showInfo === null ||
                    this.$store.state.captionData === null ||
                    this.$store.state.DICT === null ||
                    this.$store.state.HSK_WORDS === null
                )
            );
        },
        options: function() { return this.$store.state.options; },
        captionOffset: function() { return this.$store.state.captionOffset; },
        captionFontScale: function() { return this.$store.state.captionFontScale; },
        videoId: function() {
            if (this.url !== null) {
                const id = getYoutubeIdFromURL(this.url); // eslint-disable-line
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
                captionId = 'youtube-' + this.videoId;
            }
            if (this.$store.state.videoList === null || ! this.$store.state.videoList.has(captionId)) {
                return null;
            }

            return captionId;
        },
        videoFrameSize: function() {
            if (this.$store.state.captionData === null) return null;
            return this.$store.state.captionData['frame_size'];
        },
        currentCaptionIdx: function() {
            return this.getCurrentCaptionIdx(true); // with offset if any
        },
        currentBlurCaptionIdx: function() {
            return this.getCurrentCaptionIdx(false); // without offsets
        },
    },
};
</script>

<style>

#captionroot {
    position:absolute;
    z-index: 9998;
}

</style>
