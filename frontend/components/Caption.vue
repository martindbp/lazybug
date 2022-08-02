<template>
    <div>
        <CaptionContainer
            id="captionroot"
            ref="captionroot"
            :style="{ fontSize: $store.state.captionFontSize+'px !important' }"
            v-bind:isLoading="isLoading"
            v-bind:isLikelyAnAd="isLikelyAnAd"
            v-bind:currentCaptionIdx="currentCaptionIdx"
            v-bind:firstCaption="firstCaption"
            v-bind:prevCaption="prevCaption"
            v-bind:currCaption="currCaption"
            v-bind:nextCaption="nextCaption"
            v-bind:currTime="currTime"
            v-bind:paused="paused"
            v-bind:videoAPI="videoAPI"
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
        <OptionsDialog />
    </div>
</template>

<script>
import CaptionContainer from './CaptionContainer.vue'
import CaptionBlur from './CaptionBlur.vue'
import OptionsDialog from './OptionsDialog.vue'

const DEFAULT_WIDTH = 916;
const CAPTION_END_BUFFER_TIME = 1;

let lastCaptionIdxGlobal = 0;

function getClosestParentScroll($el, axis) {
    let variable = axis === 'y' ? 'scrollTop' : 'scrollLeft';
    while ($el && $el[variable] === 0) {
        $el = $el.parentElement;
    }

    if ($el) {
        return $el[variable];
    }

    return axis === 'y' ? window.scrollY : window.scrollX;
}

export default {
    mixins: [mixin],
    components: {
        CaptionContainer,
        CaptionBlur,
        OptionsDialog,
    },
    props: ['AVElement', 'captionId', 'videoDuration', 'videoAPI'],
    data: function() {
        return {
            currTime: -1000.5,
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
            translationSource: null, // human vs. machine
            pauseDuration: null,
            keyboardListener: null,
        };
    },
    mounted: function() {
        this.setUpdateInterval();
        this.setObserversAndHandlers();
    },
    beforeDestroy: function() {
        clearInterval(this.currentTimeInterval);
        window.removeEventListener('load', this.updateCaptionPositionBlur);
        window.removeEventListener('keydown', this.keyboardListener);
        document.removeEventListener('fullscreenchange', this.fullscreenChangeListener);
        if (this.mutationObserver !== null) this.mutationObserver.disconnect();
        if (this.resizeObserver !== null) this.resizeObserver.disconnect();
    },
    beforeUpdate: function() {
        if ([null, undefined].includes(this.$refs.captionroot) || [null, undefined].includes(this.$refs.captionroot.$el)) return;

        if (this.currCaption === null && this.minHeight === null) {
            // Since we're changing to an empty caption from a non-empty one, we transfer the min height to the empty one,
            // so it doesn't collapse
            let rect = this.$refs.captionroot.$el.getBoundingClientRect();
            this.minHeight = rect.height;
        }
    },
    updated: function() {
        // New text may have changed the size of the caption, so need to update the position
        const self = this;
        this.$nextTick(function () {
            self.updateCaptionPositionBlur();
            if (! [null, undefined].includes(self.$refs.captionroot) && ! [null, undefined].includes(self.$refs.captionroot.$el)) {
                self.$refs.captionroot.$el.style.minHeight = self.minHeight === null ? '0px' : self.minHeight + 'px';

                // Make sure the root is always as wide as the menu
                const menuWidth = self.$refs.captionroot.$refs.menu.$el.getBoundingClientRect().width;
                self.$refs.captionroot.$el.style.minWidth = menuWidth + 'px';
            }
        });
    },
    watch: {
        captionId: {
            immediate: true,
            handler: function() {
                this.$store.commit('setCaptionId', this.captionId);
                this.fetchCaptionMaybe();
                lastCaptionIdxGlobal = 0;
            }
        },
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

                this.resizeObserver = new ResizeObserver(this.updateCaptionPositionBlur)
                this.resizeObserver.observe(newValue);
            }
        },
        '$store.state.videoList': {
            immediate: true,
            handler: function() {
                this.fetchCaptionMaybe();
            }
        },
        captionOffset: function() {
            this.updateCaptionPositionBlur();
        },
        captionFontScale: function() {
            this.updateCaptionPositionBlur();
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
            if (this.captionId === null) {
                this.$store.commit('setCaptionIdDataHash', {id: null, data: null, hash: null});
                return;
            }
            if (this.$store.state.captionHash === 'fetching') return;
            if (this.$store.state.fetchedCaptionId === this.captionId) return;

            this.$store.commit('resetResourceFetchError', 'caption data');
            this.$store.commit('setCaptionIdDataHash', {id: null, data: null, hash: 'fetching'});

            const self = this;
            const captionId = self.captionId;
            fetchCaptions(captionId, function (message) {
                if (self.$store.state.fetchedCaptionId === self.captionId) return true;

                if (message === 'error') {
                    self.$store.commit('setResourceFetchError', 'caption data');
                    self.$store.commit('setCaptionIdDataHash', {id: null, data: null, hash: null});
                    return false;
                }
                self.$store.commit('resetResourceFetchError', 'caption data');
                if (self.$store.state.captionHash === message.hash) return true;

                message.id = captionId;

                self.$store.commit('setCaptionIdDataHash', message);
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
            window.addEventListener('load', this.updateCaptionPositionBlur);
            document.addEventListener('fullscreenchange', this.fullscreenChangeListener);

            // Update the caption position on any changes to the page (except to the caption itself), since there is no way to
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
                    self.updateCaptionPositionBlur();
                }
            })
            this.mutationObserver.observe(document, {subtree: true, childList: true});

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
            this.updateCaptionPositionBlur();
        },
        setUpdateInterval: function() {
            const self = this;
            self.currentTimeInterval = setInterval(() => {
                if (self.AVElement === null || self.$store.state.captionData == null) return;
                const newTime = self.videoAPI.getCurrentTime();
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
                    self.videoAPI.pause();
                }
                else if (self.options.autoPause === 'WPS' && canPause && wordsPerSecond > self.options.WPSThreshold) {
                    self.automaticallyPausedThisCaption = true;
                    self.videoAPI.pause();
                    const c = self.currCaption || self.prevCaption;
                    self.pauseDuration = c.alignments.length / self.options.WPSThreshold - (newTime - c.t0);
                    console.log('PAUSING FOR', self.pauseDuration);
                    setTimeout(function() {
                        if (self.pauseDuration !== null) {
                            self.videoAPI.play(); // resume
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
        updateCaptionPositionBlur: function() {
            if ([null, undefined].includes(this.AVElement) || [null, undefined].includes(this.$refs.captionroot)) return;
            let videoRect = this.AVElement.getBoundingClientRect();
            let scrollY = getClosestParentScroll(this.$refs.captionroot.$el, 'y');
            let scrollX = getClosestParentScroll(this.$refs.captionroot.$el, 'x');
            this.$refs.captionroot.$el.style.left = ((videoRect.left+scrollX) + 0.1 * videoRect.width + this.captionOffset[0]) + 'px';
            this.$refs.captionroot.$el.style.top = (0.8 * (videoRect.bottom+scrollY) + this.captionOffset[1]) + 'px';
            if (this.$refs.blurroot) {
                this.$refs.blurroot.updateBlurStyle();
            }
        },
        getCurrentCaptionIdx: function(withTimingOffset) {
            const captionData = this.$store.state.captionData;
            if (captionData === null) return null;

            const lines = captionData.lines;
            const lastSeenCaption = captionArrayToDict(lines[lastCaptionIdxGlobal], captionData);
            const lastSeenCaptionT0 = lastSeenCaption.t0 + (withTimingOffset ? lastSeenCaption.timingOffset : 0);
            if (this.currTime < lastSeenCaptionT0) {
                // Start over search from the beginning
                lastCaptionIdxGlobal = 0;
            }

            for (let i = lastCaptionIdxGlobal; i < lines.length; i++) {
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
            if ([null, undefined, 0, NaN].includes(this.videoDuration) || this.$store.state.captionData === null) return false;

            const captionDuration = this.$store.state.captionData.video_length;
            // Youtube iFrame API has a duration resolution of 1s
            const isAd = Math.abs(this.videoDuration - captionDuration) > 1.1;
            console.log('Is ad:', isAd);
            return isAd;
        },
        firstCaption: function() {
            const data = this.$store.state.captionData;
            if (data !== null && data.lines.length > 0) {
                return captionArrayToDict(data.lines[0], this.$store.state.captionData);
            }
        },
        isLoading: function() {
            return (
                this.captionId !== null && (
                    this.$store.state.videoList === null ||
                    getShowInfo(this.$store) === null ||
                    this.$store.state.captionData === null ||
                    this.$store.state.DICT === null ||
                    this.$store.state.HSK_WORDS === null
                )
            );
        },
        options: function() { return this.$store.state.options; },
        captionOffset: function() { return this.$store.state.captionOffset; },
        captionFontScale: function() { return this.$store.state.captionFontScale; },
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
    z-index: 6000;
    font-size: 24px !important;
    padding: 0 !important;
}

</style>
