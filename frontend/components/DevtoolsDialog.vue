<template>
    <q-dialog seamless persistent position="top" v-model="show">
        <q-card>
            <div v-if="captionRect">
                top: {{captionRect.top.toFixed(2)}}
                bottom: {{captionRect.bottom.toFixed(2)}}
                left: {{captionRect.left.toFixed(2)}}
                right: {{captionRect.right.toFixed(2)}}
            </div>
            <q-btn flat label="Measure Caption" @click="measureCaption"></q-btn>
            <q-btn flat :label="recording? 'Stop' : 'Record'" @click="toggleRecording"></q-btn>
            <q-btn flat label="Close" @click="show = false"></q-btn>
        </q-card>
    </q-dialog>
</template>

<script>


export default {
    mixins: [mixin],
    data: function() { return {
        keyboardListener: null,
        captionRect: null,
        recording: false,
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
            return document.querySelector(this.AVElementSelector);
        },
        videoMenuSelector: function() {
            return this.getSiteString('videoMenuSelector');
        },
        videoMenuElement: function() {
            return document.querySelector(this.videoMenuSelector);
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
        toggleRecording: function() {
            let flashDiv = document.createElement("div");
            flashDiv.style.cssText = "position:absolute;";
            document.body.appendChild(flashDiv);

            flashDiv.style.left = mouseDownClientX + "px";
            flashDiv.style.top = mouseDownClientY + "px";
            flashDiv.style.width = (captionRightPx - captionLeftPx) + "px";
            flashDiv.style.height = (captionBottomPx - captionTopPx) + "px";
            flashDiv.style.background = 'rgb(0, 255, 0)';
            timings = [];
            setTimeout(function() {
                flashDiv.remove();
                const start = window.performance.now() / 1000;
                let interval = setInterval(function() {
                    if (timings === null) {
                        clearInterval(interval);
                        return;
                    }
                    const offset = window.performance.now() / 1000 - start;
                    console.log(offset, AVElement.currentTime, AVElement.duration);
                    timings.push([offset, AVElement.currentTime, AVElement.duration]);
                }, 500);
            }, 100);
        },
        measureCaption: function() {
            const self = this;
            this.captionRect = null;
            if (this.videoMenuElement) this.videoMenuElement.style.visibility = 'hidden';

            let clientX = null;
            let clientY = null;
            let mouseDownClientX = null;
            let mouseDownClientY = null;
            let measureDiv = null;
            let moveHandler = null;
            let scrollX = getClosestParentScroll(this.AVElement, 'x');
            let scrollY = getClosestParentScroll(this.AVElement, 'y');
            window.addEventListener("mousemove", function(event) {
                clientX = event.clientX;
                clientY = event.clientY;
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
                //measureDiv.remove();
                measureDiv = null;
                window.removeEventListener("mousemove", moveHandler);
                moveHandler = null;
                if (self.videoMenuElement) self.videoMenuElement.style.visibility = 'visible';

                self.captionRect = {
                    top: captionTop,
                    bottom: captionBottom,
                    left: captionLeft,
                    right: captionRight,
                };
            }

            function startMeasuring() {
                console.log('Start measuring');
                measureDiv = document.createElement("div");
                measureDiv.style.cssText = "position:absolute; color: white; border-color: black; border: 2px solid black; z-index: 9999";
                document.body.appendChild(measureDiv);

                mouseDownClientX = clientX;
                mouseDownClientY = clientY;
                measureDiv.style.left = clientX + "px";
                measureDiv.style.top = clientY + "px";
                measureDiv.style.width = 0 + "px";
                measureDiv.style.height = 0 + "px";

                moveHandler = (moveEvent) => {
                    measureDiv.style.width = (moveEvent.clientX - mouseDownClientX) + "px";
                    measureDiv.style.height = (moveEvent.clientY - mouseDownClientY) + "px";
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
