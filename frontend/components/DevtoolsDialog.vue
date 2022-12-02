<template>
    <q-dialog seamless persistent position="top" v-model="show">
        <q-card>
            <div v-if="! recording">
                <q-input v-model="videoElementSelector" label="Video Element Selector" />
                <span v-if="AVElement === null">
                    No Video Element Found
                </span>

                <q-input
                    filled
                    color="purple-12"
                    v-model="showId"
                    label="Show ID"
                    bottom-slots
                    hint="Press TAB to autocomplete"
                    :error-message="showIdErrorMessage"
                    :error="showIdErrorMessage !== null"
                    :shadow-text="inputShadowText"
                    @keydown="processInputFill"
                    @focus="processInputFill"
                />
            </div>
            <div v-if="! recording && AVElement">
                <q-list bordered separator>
                    <q-item clickable v-ripple v-for="(rect, idx) of captionRects">
                        <q-item-section>
                            <b>Caption {{ idx + 1}}:</b>
                            top={{parseInt(100*rect.top, 10)}}%
                            bottom={{parseInt(100*rect.bottom, 10)}}%
                            left={{parseInt(100*rect.left, 10)}}%
                            right={{parseInt(100*rect.right, 10)}}%
                            <q-btn style="width: 100px" label="Remove" color="red" @click="removeCaption(idx)"></q-btn>
                        </q-item-section>
                    </q-item>
                    <q-item>
                        <q-btn flat label="Add Caption" @click="addCaption"></q-btn>
                    </q-item>
                </q-list>

                <CaptionRect v-for="rect of captionRects" :AVElement="AVElement" :measureRect="rect" />

                <q-btn v-if="captionElements.length > 0" flat label="Clear Captions" @click="clearCaptions"></q-btn>
                <q-btn flat v-if="captionElements.length > 0" label="Start Recording" @click="startRecording"></q-btn>
                <q-btn flat v-if="recordedTimings.length > 0" label="Clear Timings" @click="this.recordedTimings = []"></q-btn>

                <q-btn flat v-if="recordedTimings.length > 0" :label="(showTimings ? 'Hide' : 'Show') + ' Timings'" @click="showTimings = !showTimings"></q-btn>
                <q-scroll-area v-if="showTimings" style="height: 200px;">
                    <div v-for="t in recordedTimings">{{ t }}</div>
                </q-scroll-area>

                <q-btn flat :label="(showData ? 'Hide' : 'Show') + ' Data'" @click="showData = !showData"></q-btn>
                <q-scroll-area v-if="showData" style="height: 200px;">
                    {{ allShows[showId] === undefined ? 'Nothing here' : allShows[showId] }}
                </q-scroll-area>

                <q-btn flat label="Save" @click="save"></q-btn>
                <q-btn flat label="Close" @click="show = false"></q-btn>
            </div>
            <div v-else>
                <q-btn flat v-if="recording" label="Stop Recording" @click="stopRecording"></q-btn>
            </div>
        </q-card>
    </q-dialog>
</template>

<script>
import CaptionRect from './CaptionRect.vue'

function syncShows(data) {
    setIndexedDbData('other', ['devtoolShows'], [data], function() {});
}

function getShows(callback) {
    getIndexedDbData('other', ['devtoolShows'], callback);
}

export default {
    mixins: [mixin],
    component: {
        CaptionRect,
    },
    data: function() { return {
        keyboardListener: null,
        captionRects: [],
        recording: false,
        captionElements: [],
        recordedTimings: [],
        showTimings: false,
        showData: false,
        videoElementSelector: null,
        shows: {},
        showId: null,
    }},
    computed: {
        inputShadowText: function() {
            if (this.showId === null) return null;
            for (const id of this.allShowIds) {
                if (id.startsWith(this.showId)) {
                    const left = id.slice(this.showId.length);
                    if (left.length === 0) return null;
                    else return left;
                }
            }
            return null;
        },
        showIdErrorMessage: function() {
            const v = this.showId;
            if (v === null) return null;
            else if (v.length > 0 && ! v.match(/^[a-z0-9]+$/)) {
                return 'Please use lowercase alpha-numeric characters only';
            }
            return null;
        },
        show: {
            get: function() { return this.$store.state.showDialog.devtools; },
            set: function(val) { this.$store.commit('setShowDialog', {dialog: 'devtools', val: val}); },
        },
        AVElementSelector: function() {
            return this.getSiteString('AVElementSelector');
        },
        AVElement: function() {
            return document.querySelector(this.videoElementSelector);
        },
        videoMenuSelector: function() {
            return this.getSiteString('videoMenuSelector');
        },
        videoMenuElement: function() {
            return document.querySelector(this.videoMenuSelector);
        },
        allShowIds: function() {
            return Object.keys(this.shows).concat(this.remoteShowIds);
        },
        allShows: function() {
            return Object.assign({}, this.shows, this.remoteShows)
        },
        remoteShows: function() {
            return this.$store.state.showList || {};
        },
        remoteShowIds: function() {
            return Object.keys(this.remoteShows);
        },
    },
    watch: {
        AVElementSelector: function() {
            if (this.AVElementSelector) this.videoElementSelector = this.AVElementSelector;
        },
        shows: function() {
            //syncShows(this.shows);
        },
    },
    mounted: function() {
        const self = this;
        this.keyboardListener = window.addEventListener("keydown", function(event) {
            const shift = event.getModifierState("Shift");
            const ctrl = event.getModifierState("Control");
            const alt = event.getModifierState("Alt");
            console.log(shift, ctrl, alt, event.key);
            if (shift && ctrl && alt && event.key === 'D') {
                self.show = true;
            }
        }, {capture: true});

        getShows(function(data) {
            self.shows = data;
        });
    },
    beforeDestroy: function() {
        window.removeEventListener('keydown', this.keyboardListener);
    },
    methods: {
        save: function() {
            let show = this.shows[this.showId];
            if (show === undefined) {
                this.shows[this.showId] = {
                    "name": {
                        "hz": "",
                        "py": "",
                        "en": ""
                    },
                    "date_added": "",
                    "douban": 0.0,
                    "year": "",
                    "type": "tv",
                    "genres": [],
                    "synopsis": "",
                    "caption_source": "",
                    "translation_source": "",
                    "released": false,
                    "seasons": [
                        {
                            "episodes": [{}]
                        },
                    ]
                };
                show = this.shows[this.showId];
            }

            if (this.captionRects.length > 0) {
                show["ocr_params"] = this.captionRects.map(function (r) {
                    return {
                        "type": "hanzi",
                        "caption_top": r.top,
                        "caption_bottom": r.bottom,
                        "caption_left": r.left,
                        "caption_right": r.right,
                        "start_time": 0
                    }
                });
            }

            const seasons = show.seasons;
            const episodes = seasons[seasons.length-1].episodes;
            const id = extractCurrentVideoId(this.$store.state.STRINGS, window.location.href);
            const episode = episodes[episodes.length-1];
            episode.id = id;

            if (this.recordedTimings.length > 0) {
                episode.timings = this.recordedTimings;
            }

            syncShows(this.shows);
        },
        processInputFill: function(e) {
            if (e.keyCode === 9 && this.inputShadowText !== null) {
                this.showId = this.showId + this.inputShadowText;
                this.inputShadowText = null;
            }
        },
        removeCaption: function(idx) {
            this.captionElements[idx].remove();
            this.captionElements.splice(idx, 1);
            this.captionRects.splice(idx, 1);
        },
        clearCaptions: function() {
            for (const $el of this.captionElements) {
                $el.remove();
            }
            this.captionElements = [];
            this.captionRects = [];
        },
        startRecording: function() {
            this.recording = true;
            for (const captionEl of this.captionElements) {
                captionEl.style.background = 'rgb(0, 255, 0)';
                captionEl.style.visibility = 'visible';
            }
            this.recordedTimings = [];
            const self = this;
            setTimeout(function() {
                // Hide the divs after 100 ms green flashing
                for (const captionEl of self.captionElements) {
                    captionEl.style.visibility = 'hidden';
                }
                const start = window.performance.now() / 1000;
                let interval = setInterval(function() {
                    const offset = window.performance.now() / 1000 - start;
                    const timing = [offset, self.AVElement.currentTime, self.AVElement.duration, self.AVElement.paused];
                    if (self.recordedTimings.length === 0) {
                        self.recordedTimings.push(timing);
                        return;
                    }
                    const currentTime = self.AVElement.currentTime;
                    const duration = self.AVElement.duration;
                    const paused = self.AVElement.paused;
                    const [lastOffset, lastCurrentTime, lastDuration, lastPaused] = self.recordedTimings[self.recordedTimings.length-1];
                    const offsetDelta = offset - lastOffset;
                    const videoDelta = currentTime - lastCurrentTime;
                    const pausedNoChange = paused && lastPaused
                    if (! self.recording || (! pausedNoChange  && (duration !== lastDuration || Math.abs(offsetDelta - videoDelta) > 0.1))) {
                        console.log('Adding', timing);
                        self.recordedTimings.push(timing);
                    }

                    if (! self.recording) {
                        clearInterval(interval);
                        // Restore divs
                        for (const captionEl of self.captionElements) {
                            captionEl.style.background = 'transparent';
                            captionEl.style.visibility = 'visible';
                        }
                        return;
                    }
                }, 500);
            }, 100);
        },
        stopRecording: function() {
            this.recording = false;
        },
        addCaption: function() {
            const self = this;
            if (this.videoMenuElement) this.videoMenuElement.style.visibility = 'hidden';

            let clientX = null;
            let clientY = null;
            let mouseDownClientX = null;
            let mouseDownClientY = null;
            let moveHandler = null;
            let scrollX = getClosestParentScroll(this.AVElement, 'x');
            let scrollY = getClosestParentScroll(this.AVElement, 'y');
            window.addEventListener("mousemove", function(event) {
                clientX = event.clientX + scrollX;
                clientY = event.clientY + scrollY;
            });

            function stopMeasuring() {
                console.log('Stop measuring');
                videoRect = self.AVElement.getBoundingClientRect();
                captionTopPx = mouseDownClientY - videoRect.top;
                captionTop = captionTopPx / videoRect.height;
                captionBottomPx = clientY - videoRect.top;
                captionBottom = captionBottomPx / videoRect.height;
                captionLeftPx = mouseDownClientX - videoRect.left;
                captionLeft = captionLeftPx / videoRect.width;
                captionRightPx = clientX - videoRect.left;
                captionRight = captionRightPx / videoRect.width;
                window.removeEventListener("mousemove", moveHandler);
                moveHandler = null;
                if (self.videoMenuElement) self.videoMenuElement.style.visibility = 'visible';

                self.captionRects.push({
                    top: captionTop,
                    bottom: captionBottom,
                    left: captionLeft,
                    right: captionRight,
                });
            }

            function startMeasuring() {
                console.log('Start measuring');
                const captionEl = document.createElement("div");
                self.captionElements.push(captionEl);
                captionEl.style.cssText = "position: absolute; color: white; border-color: black; border: 2px solid black; z-index: 9999";
                document.body.appendChild(captionEl);

                mouseDownClientX = clientX;
                mouseDownClientY = clientY;
                captionEl.style.left = clientX + "px";
                captionEl.style.top = clientY + "px";
                captionEl.style.width = 0 + "px";
                captionEl.style.height = 0 + "px";

                moveHandler = (moveEvent) => {
                    captionEl.style.width = ((moveEvent.clientX+scrollX) - mouseDownClientX) + "px";
                    captionEl.style.height = ((moveEvent.clientY+scrollY) - mouseDownClientY) + "px";
                };

                window.addEventListener("mousemove", moveHandler);
                window.addEventListener("mouseup", (upEvent) => {
                    upEvent.preventDefault();
                    upEvent.stopPropagation();
                    stopMeasuring();
                }, { once: true, capture: true });
            }

            window.addEventListener("mousedown", (downEvent) => {
                downEvent.preventDefault();
                downEvent.stopPropagation();
                startMeasuring();
            }, { once: true, capture: true });
        },
    },
}
</script>
<style>
</style>
