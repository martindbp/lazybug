<template>
    <div v-if="captionData !== null">
        <CaptionContainer
            id="captionroot"
            ref="captionroot"
            :style="{ fontSize: captionFontSize+'px' }"
            v-bind:prevCaption="prevCaption"
            v-bind:currCaption="currCaption"
            v-bind:nextCaption="nextCaption"
            v-bind:currTime="currTime"
            v-bind:paused="paused"
            v-bind:AVElement="AVElement"
            v-on:seeked="seekedFromMenu = true"
        />
        <CaptionBlur
            id="blurroot"
            ref="blurroot"
            v-bind:prevCaption="prevCaption"
            v-bind:currCaption="currCaption"
            v-bind:nextCaption="nextCaption"
            v-bind:currTime="currTime"
            v-bind:AVElement="AVElement"
            v-bind:videoFrameSize="videoFrameSize"
            v-bind:videoCaptionTopPx="videoCaptionTopPx"
        />
    </div>
</template>

<script>
import CaptionContainer from './CaptionContainer.vue'
import CaptionBlur from './CaptionBlur.vue'

const DEFAULT_FONT_SIZE = 16;
const DEFAULT_WIDTH = 916;
const CAPTION_END_BUFFER_TIME = 1;

let lastCaptionIdxGlobal = 0;

function captionArrayToDict(arr) {
    let [texts, t0s, t1s, boundingRects, charProbs, logprob, data_hash, translations, alignments] = arr;
    return {
        texts: texts,
        t0s: t0s,
        t1s: t1s,
        t0: t0s[0],
        t1: t1s[t1s.length-1],
        boundingRects: boundingRects,
        charProbs: charProbs,
        logprob: logprob,
        data_hash: data_hash,
        translations: translations,
        alignments: alignments,
    };
}

export default {
    components: {CaptionContainer, CaptionBlur},
    data: function() {
        return {
            AVElementSelector: 'video',
            url: window.location.href,
            captionData: null,
            localVideoHash: null,
            currTime: -1000.5,
            AVElement: null,
            resizeObserver: null,
            mutationObserver: null,
            paused: null,
            lastPausedAt: null,
            automaticallyPausedThisCaption: false,
            minHeight: null,
            captionFontSize: null,
            seeked: false,
            showList: null,
            prevCaption: null,
            currCaption: {
                dummy: true,
                texts: [['你好你好你好你好你好']],
                t0s: [-1000],
                t1s: [-1001],
                t0: -1000,
                t1: -1001,
                boundingRects: [],
                charProbs: [],
                logprob: [],
                data_hash: null,
                translations: [['hello hello hello hello hello']],
                alignments: [
                    [0, 1, '你', [['nǐ', 'ni3']], 'you'], [1, 2, '好', [['hǎo', 'hao3']], 'good'],
                    [2, 3, '你', [['nǐ', 'ni3']], 'you'], [3, 4, '好', [['hǎo', 'hao3']], 'good'],
                    [4, 5, '你', [['nǐ', 'ni3']], 'you'], [5, 6, '好', [['hǎo', 'hao3']], 'good'],
                    [6, 7, '你', [['nǐ', 'ni3']], 'you'], [7, 8, '好', [['hǎo', 'hao3']], 'good'],
                    [8, 9, '你', [['nǐ', 'ni3']], 'you'], [9, 10, '好', [['hǎo', 'hao3']], 'good'],
                ],
            },
            nextCaption: null,
        };
    },
    mounted: function(){
        this.setUpdateInterval();
        this.AVElement = document.querySelector(this.AVElementSelector);
        this.setObserversAndHandlers();
        const self = this;
        fetchVersionedResource('show_list.json', function (data) { self.showList = data; });
    },
    beforeDestroy: function() {
        clearInterval(this.currentTimeInterval);
        window.removeEventListener('load', this.updateCaptionPositionBlurFontSize);
        document.removeEventListener('fullscreenchange', this.fullscreenChangeListener);
        if (this.mutationObserver !== null) this.mutationObserver.disconnect();
        if (this.resizeObserver !== null) this.resizeObserver.disconnect();
    },
    beforeUpdate: function() {
        if (this.$refs.captionroot === undefined || this.$refs.captionroot.$el === undefined) return;

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
            if (self.$refs.captionroot !== undefined && self.$refs.captionroot.$el !== undefined) {
                self.$refs.captionroot.$el.style.minHeight = self.minHeight === null ? '0px' : self.minHeight + 'px';

                // Make sure the root is always as wide as the menu
                const menuWidth = self.$refs.captionroot.$refs.leftmenu.$el.getBoundingClientRect().width;
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
                this.fetchCaptionMaybe();
            }
        },
        showList: {
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

            if (this.captionData === null || this.currentCaptionIdx === null) {
                this.prevCaption = null;
            }
            else if (Array.isArray(this.currentCaptionIdx)) {
                const prevIdx = this.currentCaptionIdx[0];
                if (prevIdx !== null) {
                    this.prevCaption = captionArrayToDict(this.captionData.lines[prevIdx]);
                }
            }
            else if (this.currentCaptionIdx > 0) {
                this.prevCaption = captionArrayToDict(this.captionData.lines[this.currentCaptionIdx - 1]);
            }
            else {
                this.prevCaption = null;
            }

            if (this.captionData === null || this.currentCaptionIdx === null || Array.isArray(this.currentCaptionIdx)) {
                if (this.currCaption !== null && this.currCaption.dummy !== true) {
                    this.currCaption = null;
                    this.minHeight = null;  // when the caption changes we reset any min height set
                }
            }
            else {
                this.currCaption = captionArrayToDict(this.captionData.lines[this.currentCaptionIdx]);
                this.minHeight = null;  // when the caption changes we reset any min height set
                this.automaticallyPausedThisCaption = false;
            }

            if (this.captionData === null || this.currentCaptionIdx === null) {
                this.nextCaption = null;
            }
            else if (Array.isArray(this.currentCaptionIdx)) {
                const nextIdx = this.currentCaptionIdx[1];
                if (nextIdx !== null) {
                    this.nextCaption = captionArrayToDict(this.captionData.lines[nextIdx]);
                }
            }
            else if (this.currentCaptionIdx < this.captionData.lines.length - 1) {
                this.nextCaption = captionArrayToDict(this.captionData.lines[this.currentCaptionIdx + 1]);
            }
            else {
                this.nextCaption = null;
            }
        },
    },
    methods: {
        fetchCaptionMaybe: function() {
            this.captionData = null;
            if (this.captionId === null) return;

            if (this.showList === null || ! this.showList.includes(this.captionId)) {
                // TODO: if list changes, we need to check again
                return;
            }

            const self = this;
            chrome.runtime.sendMessage({'type': 'getCaptions', 'data': {
                'captionId': self.captionId,
            }}, function onResponse(message) {
                if (message === 'error') {
                    return false;
                }
                self.captionData = message.data;
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
                    for(let mutation of mutations) {
                        for(let node of mutation.addedNodes) {
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
                        for(let node of mutation.removedNodes) {
                            if (node == self.AVElement) {
                                break;
                            }
                        }
                    }
                }
            })
            this.mutationObserver.observe(document, {subtree: true, childList: true});

            document.addEventListener('DOMContentLoaded', () => {
                self.AVElement = document.querySelector(self.AVElementSelector);
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
                if (self.AVElement === null || self.captionData == null) return;
                const newTime = self.AVElement.currentTime;
                if (self.paused && self.automaticallyPausedThisCaption && ! self.seeked && ! self.seekedFromMenu) {
                    return;
                }

                const captionChanged = (
                    (self.currCaption !== null && newTime >= self.currCaption.t1 + CAPTION_END_BUFFER_TIME) ||
                    (
                        self.nextCaption !== null &&
                        newTime >= self.nextCaption.t0 &&
                        newTime <= self.nextCaption.t1
                    )
                );
                const isDummy = self.currCaption !== null && self.currCaption.dummy === true;

                if (
                    self.options.pauseAfterCaption &&
                    ! self.automaticallyPausedThisCaption &&
                    ! self.paused &&
                    captionChanged &&
                    ! self.seeked &&
                    ! self.seekedFromMenu &&
                    ! isDummy
                ) {
                    self.AVElement.pause();
                    self.automaticallyPausedThisCaption = true;
                }
                else {
                    self.currTime = newTime;
                }
                self.seeked = false;
            }, 10);
        },
        updateCaptionPositionBlurFontSize: function() {
            if (this.AVElement === null || this.$refs.captionroot === undefined) return;
            var videoRect = this.AVElement.getBoundingClientRect();
            // var captionRect = this.$refs.captionroot.$el.getBoundingClientRect();
            this.$refs.captionroot.$el.style.left = (videoRect.left + 0.1 * videoRect.width + this.captionOffset[0]) + 'px';
            this.$refs.captionroot.$el.style.top = (0.8 * videoRect.bottom + this.captionOffset[1]) + 'px';
            this.$refs.blurroot.updateBlurStyle();

            // We scale the font size with the width of the video element and the font scale selected by the user.
            // At width=DEFAULT_WIDTH and fontScale=0.5 we want fontSize=DEFAULT_FONT_SIZE
            this.captionFontSize = Math.round(2 * DEFAULT_FONT_SIZE * this.captionFontScale * (this.AVElement.getBoundingClientRect().width / DEFAULT_WIDTH));
        },
    },
    computed: {
        options: function() { return this.$store.state.options; },
        captionOffset: function() { return this.$store.state.captionOffset; },
        captionFontScale: function() { return this.$store.state.captionFontScale; },
        captionId: function() {
            if (this.localVideoHash !== null) {
                return 'local-' + this.localVideoHash;
            }

            let videoId = getYoutubeIdFromURL(this.url); // eslint-disable-line
            if (videoId !== null) {
                return 'youtube-' + videoId;
            }

            return null;
        },
        videoFrameSize: function() {
            if (this.captionData === null) return null;
            return this.captionData['frame_size']
        },
        videoCaptionTopPx: function() {
            if (this.captionData === null || this.videoFrameSize === undefined) return null;
            return Math.round(this.captionData['caption_top'] * this.videoFrameSize[0]);
        },
        currentCaptionIdx: function() {
            if (this.captionData === null) return null;

            const lines = this.captionData.lines
            const lastCaption = captionArrayToDict(lines[lastCaptionIdxGlobal]);
            if (this.currTime < lastCaption.t0) {
                // Start over search from the beginning
                lastCaptionIdxGlobal = 0;
            }

            for (var i = lastCaptionIdxGlobal; i < lines.length; i++) {
                let caption = captionArrayToDict(lines[i]);
                let prevCaption = i > 0 ? captionArrayToDict(lines[i-1]) : null;
                if (this.currTime >= caption.t0 && this.currTime <= caption.t1) {
                    lastCaptionIdxGlobal = i;
                    return i;
                }
                else if (prevCaption && this.currTime > prevCaption.t1 && this.currTime < caption.t0) {
                    // In between two lines
                    lastCaptionIdxGlobal = i-1;

                    // If we're still close to the prevCaption, we keep it
                    if (this.currTime < Math.min(prevCaption.t1 + CAPTION_END_BUFFER_TIME, caption.t0)) {
                        return i-1;
                    }
                    return [i-1, i];
                }
            }

            if (this.currTime < captionArrayToDict(lines[0]).t0) {
                return [null, 0];
            }
            else if (this.currTime > captionArrayToDict(lines[lines.length-1]).t1) {
                return [lines.length-1, null];
            }
            return null;
        },
    },
};
</script>

<style>
#captionroot {
    position:absolute;
    z-index: 9998;
}

.zimucaptiondiv {
    color: white;
    background-color: black;
    text-align: left;
    font-family: 'Heiti SC';
    font-size: 18px;
    padding: 0px;
    min-width: 7em;
    opacity: 0.85;
}
</style>
