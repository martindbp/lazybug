<template>
    <q-dialog seamless persistent position="top" v-model="show">
        <q-card>
            <div v-if="! recording">
                <q-input v-model="videoElementSelector" label="Video Element Selector" />
                <span v-if="AVElement === null">
                    No Video Element Found
                </span>

                <q-input v-model="currentPlaylistLinkSelector" label="Playlist Link Selector" />
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

                <CaptionRect v-if="show" v-for="rect of captionRects" :AVElement="AVElement" :measureRect="rect" />

                <q-btn v-if="captionElements.length > 0" flat label="Clear Captions" @click="clearCaptions"></q-btn>
                <q-btn flat v-if="captionElements.length > 0" label="Start Recording" @click="startRecording"></q-btn>
                <q-btn flat v-if="recordedTimings.length > 0" label="Clear Timings" @click="this.recordedTimings = []"></q-btn>

                <q-btn flat v-if="recordedTimings.length > 0" label="Save Timings" @click="saveTimings"></q-btn>
                <q-btn flat :label="(showData ? 'Hide' : 'Show') + ' Data'" @click="showData = !showData"></q-btn>
                <q-scroll-area v-if="showData" style="height: 200px;">
                    <pre>{{ JSON.stringify(data, null, 2) }}</pre>
                </q-scroll-area>

                <q-btn v-if="site === 'youtube'" flat label="Import Playlist" @click="importPlaylist"></q-btn>
                <q-btn flat label="Import Episode" @click="importEpisode"></q-btn>

                <q-btn flat label="Download" @click="download"></q-btn>
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
        currentPlaylistLinkSelector: null,
        shows: {},
        data: {
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
            "seasons": []
        },
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
            set: function(val) { this.$store.commit('setShowDialog', {dialog: 'devtools', value: val}); },
        },
        AVElementSelector: function() {
            return this.getSiteString('AVElementSelector');
        },
        AVElement: function() {
            return document.querySelector(this.videoElementSelector);
        },
        playlistLinkSelector: function() {
            return this.getSiteString('playlistLinkSelector');
        },
        videoMenuSelector: function() {
            return this.getSiteString('videoMenuSelector');
        },
        videoMenuElement: function() {
            return document.querySelector(this.videoMenuSelector);
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
        playlistLinkSelector: function() {
            if (this.playlistLinkSelector) this.currentPlaylistLinkSelector = this.playlistLinkSelector;
        },
        captionRects: function() {
            if (this.captionRects.length > 0) {
                this.data["ocr_params"] = this.captionRects.map(function (r) {
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
        },
    },
    mounted: function() {
        const self = this;
        this.keyboardListener = window.addEventListener("keydown", function(event) {
            const shift = event.getModifierState("Shift");
            const ctrl = event.getModifierState("Control");
            const alt = event.getModifierState("Alt");
            console.log(shift, ctrl, alt);
            if (shift && ctrl && alt) {
                self.show = true;
            }
        }, {capture: true});
    },
    beforeDestroy: function() {
        window.removeEventListener('keydown', this.keyboardListener);
    },
    methods: {
        saveTimings: function() {
            const id = extractCurrentVideoId(this.$store.state.STRINGS, window.location.href);
            const captionId = `${site}-${id}`;
            let currEp = null;
            for (const season of this.data.seasons) {
                for (const episode of season.episodes) {
                    if (episode.id === captionId) currEp = episode;
                }
            }
            if (currEp === null) {
                currEp = {id: captionId};
                this.data.seasons[this.data.seasons.length - 1].push(currEp);
            }
            currEp.timings = this.recordedTimings;
        },
        importPlaylist: function() {
            if (this.currentPlaylistLinkSelector === null) return;
            const season = {episodes: []};
            for (var $el of document.querySelectorAll(this.currentPlaylistLinkSelector)) {
                let videoId = extractCurrentVideoId(this.$store.state.STRINGS, $el.href);
                season.episodes.push({
                    "id": `${this.site}-${videoId}`
                });
            }

            if (this.site === 'youtube') {
                const urlSearchParams = new URLSearchParams(window.location.search);
                const params = Object.fromEntries(urlSearchParams.entries());
                const playlistId = params["list"];
                season.playlist_id = playlistId;
            }

            this.data.seasons.push(season);
        },
        importEpisode: function() {
            const id = extractCurrentVideoId(this.$store.state.STRINGS, window.location.href);
            const episode = {id: `${this.site}-${id}`};
            this.data.seasons.push([episode]);
        },
        download: function() {
            download('show.json', this.data);
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
