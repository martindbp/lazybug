<template>
    <div>
        <CaptionContainer
            id="captionroot"
            ref="captionroot"
            :class="{ docked: $store.state.captionDocked }"
            :style="{ fontSize: $store.state.options.captionFontSize+'px !important' }"
            v-bind:playerId="playerId"
            v-bind:isLoading="isLoading"
            v-bind:isLikelyAnAd="isLikelyAnAd"
            v-bind:firstCaption="firstCaption"
            v-bind:prevCaption="prevCaption"
            v-bind:currCaption="currCaption"
            v-bind:nextCaption="nextCaption"
            v-bind:currTime="currTime"
            v-bind:paused="paused"
            v-bind:pauseDuration="pauseDuration"
            v-on:seeked="seekedFromMenu = true"
            v-on:mouseOver="pauseDuration = null"
        />
        <CaptionRect
            id="blurroot"
            ref="blurroot"
            v-if="captionData !== null && $store.state.extensionOn"
            v-bind:playerId="playerId"
            v-bind:prevCaption="prevCaption"
            v-bind:currCaption="currCaption"
            v-bind:nextCaption="nextCaption"
            v-bind:currTime="currTime"
            v-bind:AVElement="AVElement"
            v-bind:videoFrameSize="videoFrameSize"
        />
        <OptionsDialog :playerId="playerId" />
    </div>
</template>

<script>
import CaptionContainer from './CaptionContainer.vue'
import CaptionRect from './CaptionRect.vue'
import OptionsDialog from './OptionsDialog.vue'

const DEFAULT_WIDTH = 916;
const CAPTION_END_BUFFER_TIME = 1;

export default {
    mixins: [mixin],
    components: {
        CaptionContainer,
        CaptionRect,
        OptionsDialog,
    },
    props: [
        'playerId',
        'AVElement',
        'captionId',
        'videoDuration',
    ],
    data: function() {
        return {
            currTime: -1000.5,
            resizeObserver: null,
            mutationObserver: null,
            paused: null,
            lastPausedAt: null,
            automaticallyPausedThisCaption: false,
            minHeight: null,
            seeked: false,
            seekedFromMenu: false,
            prevCaption: null,
            currCaption: null,
            nextCaption: null,
            translationSource: null, // human vs. machine
            pauseDuration: null,
            keyboardListener: null,
            sentNextVideoEvent: false,
        };
    },
    mounted: function() {
        this.setUpdateInterval();
        this.setObserversAndHandlers();
        this.updateCaptionPositionBlur();
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
        if (isNone(this.$refs.captionroot) || isNone(this.$refs.captionroot.$el)) return;

        if (isNone(this.currCaption) && isNone(this.minHeight)) {
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
            if (
                ! self.$store.state.captionDocked &&
                ! isNone(self.$refs.captionroot) &&
                ! isNone(self.$refs.captionroot.$el)
            ) {
                self.$refs.captionroot.$el.style.minHeight = isNone(self.minHeight) ? '0px' : self.minHeight + 'px';

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
                this.fetchCaptionMaybe();
                this.currTime = -1000.5;
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
        captionOffset: function() {
            this.updateCaptionPositionBlur();
        },
        captionFontScale: function() {
            this.updateCaptionPositionBlur();
        },
        currentCaptionIdx: function(newIdx, oldIdx) {
            if (JSON.stringify(newIdx) === JSON.stringify(oldIdx)) return;
            console.log('currentCaptionIdx', newIdx, oldIdx);

            const captionData = this.captionData;

            if (this.playerData.reviewCaptionIndices && Array.isArray(newIdx)) {
                if (newIdx[1] !== null) {
                    // Go straight to next caption
                    const nextLine = captionArrayToDict(captionData.lines, newIdx[1], captionData);
                    this.videoAPI.setCurrentTime(nextLine.t0 + 1e-3);
                }
                else if (! this.sentNextVideoEvent) {
                    this.videoAPI.pause();
                    this.paused = true;
                    console.log('Caption', oldIdx, newIdx, this.AVElement);
                    this.sentNextVideoEvent = true;
                    this.AVElement.dispatchEvent(new Event('nextVideo'));
                }
            }
            else if (this.sentNextVideoEvent && newIdx !== null) {
                this.sentNextVideoEvent = false;
            }

            this.$store.commit('setPlayerData', {playerId: this.playerId, captionIdx: newIdx});

            if (isNone(captionData) || isNone(this.currentCaptionIdx)) {
                this.prevCaption = null;
            }
            else if (this.findPrevNextCaptionIdx(-1) !== null) {
                const prevIdx = this.findPrevNextCaptionIdx(-1);
                this.prevCaption = captionArrayToDict(captionData.lines, prevIdx, captionData);
            }
            else {
                this.prevCaption = null;
            }

            if (isNone(captionData) || isNone(this.currentCaptionIdx) || Array.isArray(this.currentCaptionIdx)) {
                if (this.currCaption !== null) {
                    this.currCaption = null;
                    this.minHeight = null;  // when the caption changes we reset any min height set
                }
            }
            else {
                this.currCaption = captionArrayToDict(captionData.lines, this.currentCaptionIdx, captionData);
                this.minHeight = null;  // when the caption changes we reset any min height set
                this.automaticallyPausedThisCaption = false;
                const dt = Date.now() - this.sessionTime;
                this.appendSessionLog([eventsMap['EVENT_SHOW_CAPTION_IDX'], this.currentCaptionIdx, dt]);
            }

            if (isNone(captionData) || isNone(this.currentCaptionIdx)) {
                this.nextCaption = null;
            }
            else if (this.findPrevNextCaptionIdx(1) !== null) {
                this.nextCaption = captionArrayToDict(captionData.lines, this.findPrevNextCaptionIdx(1), captionData);
            }
            else {
                this.nextCaption = null;
            }
        },
    },
    methods: {
        findPrevNextCaptionIdx: function(direction = -1) {
            const captionData = this.captionData;
            let currIdx = Array.isArray(this.currentCaptionIdx) ? isNone(this.currentCaptionIdx[0]) ? this.currentCaptionIdx[1] : this.currentCaptionIdx[0] : this.currentCaptionIdx;
            if (isNone(currIdx)) return null;
            if (direction < 0 && currIdx == 0) return null;
            if (direction > 0 && currIdx == captionData.lines.length - 1) return null;
            return currIdx + direction;
        },
        fetchCaptionMaybe: function() {
            if (isNone(this.captionId)) {
                this.$store.commit('setCaptionIdDataHash', {playerId: this.playerId, id: null, data: null, hash: null});
                return;
            }
            if (this.captionHash === 'fetching') return;

            this.$store.commit('resetResourceFetchError', 'caption data');
            this.$store.commit('setCaptionIdDataHash', {playerId: this.playerId, id: null, data: null, hash: 'fetching'});

            const self = this;
            const captionId = self.captionId;
            fetchCaptions(captionId, function (message) {
                if (message === 'error') {
                    self.$store.commit('setResourceFetchError', 'caption data');
                    self.$store.commit('setCaptionIdDataHash', {playerId: self.playerId, id: null, data: null, hash: null});
                    return false;
                }
                self.$store.commit('resetResourceFetchError', 'caption data');
                if (self.captionHash === message.hash) return true;

                message.id = captionId;
                message.playerId = self.playerId;

                self.$store.commit('setCaptionIdDataHash', message);
                // Append the initial pinned peek values
                for (const type of [...STATE_ORDER, 'translation']) {
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
                if (isNone(self.captionData) || isNone(self.videoAPI)) return;
                const newTime = self.videoAPI.getCurrentTime();
                if (self.paused && self.automaticallyPausedThisCaption && ! (self.seeked || self.seekedFromMenu)) {
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

                if (self.seekedFromMenu) {
                    self.seekedFromMenu = false; // need to reset
                }

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
                    if (newTime < self.currTime) {
                        console.log(self.currTime, newTime);
                    }
                    self.currTime = newTime;
                }
                self.seeked = false;
            }, 10);
        },
        updateCaptionPositionBlur: function() {
            if (isNone(this.AVElement) || isNone(this.$refs.captionroot)) return;
            let videoRect = this.AVElement.getBoundingClientRect();
            if (isNone(videoRect)) return;
            let scrollY = getClosestParentScroll(this.$refs.captionroot.$el, 'y');
            let scrollX = getClosestParentScroll(this.$refs.captionroot.$el, 'x');
            this.$refs.captionroot.$el.style.left = ((videoRect.left+scrollX) + 0.1 * videoRect.width + this.captionOffset[0]) + 'px';
            this.$refs.captionroot.$el.style.top = (0.8 * (videoRect.bottom+scrollY) + this.captionOffset[1]) + 'px';
            if (this.$refs.blurroot) {
                this.$refs.blurroot.updateStyle();
            }
        },
        getCurrentCaptionIdxRange: function(withTimingOffset) {
            const captionData = this.captionData;
            if (isNone(captionData)) return null;

            const lines = captionData.lines;
            if (lines.length == 0) return null;
            const lastSeenCaption = captionArrayToDict(lines, this.lastCaptionIdx, captionData);
            const lastSeenCaptionT0 = lastSeenCaption.t0 + (withTimingOffset ? lastSeenCaption.timingOffset : 0);
            if (this.currTime < lastSeenCaptionT0) {
                // Start over search from the beginning
                this.lastCaptionIdx = 0;
            }

            for (let i = this.lastCaptionIdx; i < lines.length; i++) {
                let caption = captionArrayToDict(lines, i, captionData);
                let captionT0 = caption.t0 + (withTimingOffset ? caption.timingOffset : 0)
                let prevCaption = i > 0 ? captionArrayToDict(lines, i-1, captionData) : null;
                if (this.currTime >= captionT0 && this.currTime <= caption.t1) {
                    this.lastCaptionIdx = i;
                    return i;
                }
                else if (prevCaption && this.currTime > prevCaption.t1 && this.currTime < captionT0) {
                    // In between two lines
                    this.lastCaptionIdx = i-1;

                    // If we're still close to the prevCaption, we keep it
                    if (this.currTime < Math.min(prevCaption.t1 + CAPTION_END_BUFFER_TIME, captionT0)) {
                        return i-1;
                    }
                    return [i-1, i];
                }
            }

            const firstCaption = captionArrayToDict(lines, 0, captionData)
            const lastCaption = captionArrayToDict(lines, lines.length - 1, captionData)
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
            if ([null, undefined, 0, NaN].includes(this.videoDuration) || isNone(this.captionData)) return false;

            const captionDuration = this.captionData.video_length;
            // Youtube iFrame API has a duration resolution of 1s
            const isAd = Math.abs(this.videoDuration - captionDuration) > 1.1;
            console.log('Is ad:', isAd);
            return isAd;
        },
        firstCaption: function() {
            const data = this.captionData;
            if (data !== null && data.lines.length > 0) {
                return captionArrayToDict(data.lines, 0, this.captionData);
            }
        },
        isLoading: function() {
            return (
                this.captionId !== null && (
                    isNone(getShowInfo(this.playerId, this.$store)) ||
                    isNone(this.captionData) ||
                    isNone(this.$store.state.DICT) ||
                    isNone(this.$store.state.HSK_WORDS)
                )
            );
        },
        options: function() { return this.$store.state.options; },
        captionOffset: function() { return this.$store.state.captionOffset; },
        captionFontScale: function() { return this.$store.state.captionFontScale; },
        videoFrameSize: function() {
            if (isNone(this.captionData)) return null;
            return this.captionData['frame_size'];
        },
        currentCaptionIdx: function() {
            return this.getCurrentCaptionIdxRange(true); // with offset if any
        },
        currentBlurCaptionIdx: function() {
            return this.getCurrentCaptionIdxRange(false); // without offsets
        },
    },
};
</script>

<style>

#captionroot {
    font-size: 24px !important;
    padding: 0 !important;
}

#captionroot:not(.docked) {
    position:absolute;
    z-index: 6000;
}

</style>
