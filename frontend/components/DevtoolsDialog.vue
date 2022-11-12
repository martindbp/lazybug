<template>
    <q-dialog seamless persistent position="top" v-model="show">
        <q-card>
            <div v-if="! recording">
                <q-input v-model="videoElementSelector" label="Video Element Selector" />
                <span v-if="AVElement === null">
                    No Video Element Found
                </span>
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

                <q-btn v-if="captionElements.length > 0" flat label="Clear Captions" @click="clearCaptions"></q-btn>
                <q-btn flat v-if="captionElements.length > 0" label="Start Recording" @click="startRecording"></q-btn>
                <q-btn flat v-if="recordedTimings.length > 0" label="Clear Timings" @click="this.recordedTimings = []"></q-btn>
                <q-btn flat v-if="!showTimings" label="Show Timings" @click="showTimings = true"></q-btn>
                <q-btn flat label="Close" @click="show = false"></q-btn>
                <q-btn flat v-if="showTimings" label="Hide Timings" @click="showTimings = false"></q-btn>
                <q-scroll-area v-if="showTimings" style="height: 200px;">
                    <div v-for="t in recordedTimings">{{ t }}</div>
                </q-scroll-area>
            </div>
            <div v-else>
                <q-btn flat v-if="recording" label="Stop Recording" @click="stopRecording"></q-btn>
            </div>
        </q-card>
    </q-dialog>
</template>

<script>


export default {
    mixins: [mixin],
    data: function() { return {
        keyboardListener: null,
        captionRects: [],
        recording: false,
        captionElements: [],
        recordedTimings: [],
        showTimings: false,
        videoElementSelector: null,
    }},
    computed: {
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
    },
    watch: {
        AVElementSelector: function() {
            if (this.AVElementSelector) this.videoElementSelector = this.AVElementSelector;
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
    },
    beforeDestroy: function() {
        window.removeEventListener('keydown', this.keyboardListener);
    },
    methods: {
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
                    if (! self.recording) {
                        clearInterval(interval);
                        // Restore divs
                        for (const captionEl of self.captionElements) {
                            captionEl.style.background = 'transparent';
                            captionEl.style.visibility = 'visible';
                        }
                        return;
                    }
                    const offset = window.performance.now() / 1000 - start;
                    console.log(offset, self.AVElement.currentTime, self.AVElement.duration);
                    self.recordedTimings.push([offset, self.AVElement.currentTime, self.AVElement.duration]);
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
