<template>
    <div :class="{ iframecontainer: true, docked: $store.state.captionDocked }">
        <div ref="videocontainer" class="videocontainer">
            <div v-show="!playerReady" class="videoloading" />
            <div v-if="$store.state.isMovingCaption && !$store.state.isLocal" class="dragsurface" />
            <div ref="player" :id="playerID" class="player">
                <div v-if="$store.state.isLocal" style="position: absolute; bottom: 0; left: 0; right: 0;">
                    <div style="margin-left: 20%">
                        <q-slider vertical-middle style="width: 80%" color="red" dark v-model="mockTime" :min="0" :max="captionDuration" :step="0.5" />
                        <q-btn vertical-middle dark color="red" v-if="mockPlaying" label="Pause" @click="setMockPlaying(false)" />
                        <q-btn vertical-middle dark color="green" v-else label="Play" @click="setMockPlaying(true)"/>
                        <span class="timelabel">{{currentTimeLabel()}}</span>
                    </div>
                </div>
            </div>
        </div>
        <EmbeddedCaption class="embeddedcaption" ref="embeddedcaption" v-show="playerReady" />
    </div>
</template>

<script>
import EmbeddedCaption from './EmbeddedCaption.vue'

const MOCK_CLOCK_SPEED = 0.01; // s
let lastT = null;

export default {
    props: ['captionId', 'width', 'height'],
    components: {
        EmbeddedCaption,
    },
    data: function() {
        return {
            playerID: 'player'+uuidv4().replaceAll('-', ''),
            player: null,
            playerReady: false,
            focusInterval: null,
            // Mock variables are used if LOCAL is true (i.e. no youtube available)
            mockPlaying: false,
            mockTime: 0.0,
            resizeObserver: null,
        };
    },
    mounted: function(){
        const self = this;
        // If the video iframe gets focus, we keyboard shortcuts stop working, so we need to refocus the caption
        const videoAPI = this.$store.state.videoAPI;
        this.focusInterval = setInterval(function() {
            if (document.activeElement.tagName === 'IFRAME' && videoAPI && ! videoAPI.isPaused()) {
                focus(self.$refs.embeddedcaption);
            }
        }, 100);

        if (LOCAL) {
            this.sustitueClock = setInterval(function() {
                if (self.mockPlaying) {
                    self.mockTime += MOCK_CLOCK_SPEED;
                    if (self.mockTime > self.captionDuration) {
                        self.mockTime = self.captionDuration;
                        self.mockPlaying = false;
                    }
                }
            }, MOCK_CLOCK_SPEED * 1000);
        }

        this.resizeObserver = new ResizeObserver(function() {
            self.$nextTick(function () {
                const captionRect = self.$refs.embeddedcaption.$el.getBoundingClientRect();
                self.$refs.videocontainer.style.height = `calc(100% - ${captionRect.height}px)`;
            });
        });
        this.resizeObserver.observe(this.$refs.embeddedcaption.$el);
    },
    beforeUnmount: function() {
        this.destroyYoutube();
        clearInterval(this.focusInterval);
        this.focusInterval = null;
    },
    watch: {
        youtubeAPIReady: {
            immediate: true,
            handler: function() {
                this.initYoutube();
            },
        },
        captionId: function() {
            this.destroyYoutube();
            this.initYoutube();
        },
        navigateToCaptionIdx: function() {
            const captionData = this.$store.state.captionData;
            const captionIdx = this.$store.state.navigateToCaptionIdx;
            const videoAPI = this.$store.state.videoAPI;
            if (! this.playerReady || captionData === null || [null, undefined].includes(captionIdx) || videoAPI === null) {
                return;
            }

            const line = captionArrayToDict(captionData.lines, captionIdx, captionData);
            this.$store.commit('setNavigateToCaptionIdx', null);
            setTimeout(function() {
                console.log('Setting videoAPI time', line.t0);
                videoAPI.setCurrentTime(line.t0 + 0.001);
                //videoAPI.play();
            }, 1000);
        },
    },
    computed: {
        navigateToCaptionIdx: function() {
            return `${this.playerReady}|${this.$store.state.navigateToCaptionIdx}|${this.$store.state.captionData}|${this.$store.state.videoAPI}`;
        },
        youtubeAPIReady: function() {
            return this.$store.state.youtubeAPIReady;
        },
        captionDuration: function() {
            if (this.$store.state.captionData === null) return 0;
            return this.$store.state.captionData.video_length;
        }
    },
    methods: {
        currentTimeLabel: function() {
            const current = secondsToTimestamp(this.getCurrentTime());
            const total = secondsToTimestamp(this.getDuration());
            return `${current} / ${total}`;
        },
        setMockPlaying: function(playing) {
            this.mockPlaying = playing;
            this.onPlayerStateChange({data: playing ? YT.PlayerState.PLAYING : YT.PlayerState.PAUSED});
        },
        destroyYoutube: function() {
            if (this.player && ! LOCAL) {
                this.player.destroy();
                this.player = null;
            }
            this.playerReady = false;
            this.mockTime = 0;
            this.mockPlaying = false;
        },
        initYoutube: function() {
            const self = this;
            if (! this.$store.state.youtubeAPIReady) return;

            if (! LOCAL) {
                console.log('initing initYoutube', this.playerID, this.captionId, document.querySelectorAll('#' + this.playerID));
                this.$nextTick(() => { // nextTick because player element may not be done
                    this.player = new YT.Player(this.playerID, {
                        width: this.width,
                        height: this.height,
                        videoId: videoIdFromCaptionId(this.captionId),
                        playerVars: {
                            'playsinline': 1,
                            'rel': 0,
                            'cc_load_policy': 3,
                            'autoplay': 1,
                            'enablejsapi': 1,
                            'origin': 'https://lazybug.ai',
                            'showinfo': 0,
                        },
                        events: {
                            'onReady': this.onReady,
                            'onStateChange': this.onPlayerStateChange,
                            'onError': this.onPlayerError,
                        }
                    });
                });
            }
            const videoAPI =  {
                getCurrentTime: this.getCurrentTime,
                setCurrentTime: this.setCurrentTime,
                getDuration: this.getDuration,
                play: this.play,
                pause: this.pause,
                isPaused: this.isPaused,
            };
            this.$store.commit('setCaptionId', this.captionId);
            this.$store.commit('setVideoAPI', videoAPI);
            if (LOCAL) {
                this.onReady();
            }
        },
        onReady: function() {
            let $el = document.getElementById(this.playerID);
            this.$store.commit('setAVElement', $el);
            this.$store.commit('setVideoDuration', this.getDuration());
            const self = this;
            // Wait a bit before setting playerReady to remove flickering because iframe hasn't fully rendered yet
            setTimeout(function() {
                console.log('playerReady');
                self.playerReady = true;
            }, 100);
        },
        onPlayerError: function(error) {
            console.log(error);
        },
        getCurrentTime: function() {
            if (! this.playerReady) return 0;
            if (LOCAL) return this.mockTime;

            let t = this.player.getCurrentTime();

            // The youtube embed API doesn't return reliable timings
            // After pausing and playing again (and at other points in time) it
            // tends to return a time that is in the past, within 200ms, so
            // if that happens we just return the last known time until the difference is
            // larger than 200 ms
            if (lastT !== null && t < lastT && lastT - t < 0.2) {
                return lastT;
            }
            lastT = t;
            return t;
        },
        setCurrentTime: function(t) {
            if (! this.playerReady) return;
            if (LOCAL) {
                this.mockTime = Math.floor(t);
                return;
            }
            this.player.seekTo(t, true); // allowSeekAhead
        },
        getDuration: function() {
            if (! this.playerReady) return 0;
            if (LOCAL) return this.captionDuration; // we have no youtube iframe, so use the time we get from caption data
            return this.player.getDuration();
        },
        play: function() {
            if (! this.playerReady) return;
            if (LOCAL) {
                this.setMockPlaying(true);
                return;
            }
            this.player.playVideo();
        },
        pause: function() {
            if (! this.playerReady) return;
            if (LOCAL) {
                this.setMockPlaying(false);
                return;
            }
            this.player.pauseVideo();
        },
        isPaused: function() {
            if (! this.playerReady) return false;
            if (LOCAL) return !this.mockPlaying;
            return this.player.getPlayerState() === 2;
        },
        onPlayerStateChange: function(event) {
            if ([null, undefined].includes(this.$store.state.AVElement)) return;
            if (event.data === YT.PlayerState.PLAYING) {
                this.$store.state.AVElement.dispatchEvent(new Event('play'));
            }
            else if (event.data === YT.PlayerState.PAUSED) {
                this.$store.state.AVElement.dispatchEvent(new Event('pause'));
            }
        },
    },
};
</script>

<style>
.iframecontainer {
    position: relative;
    height: 100%;
}

.iframecontainer > iframe {
    z-index: 0;
}

.dragsurface {
    z-index: 98;
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0);
}

.videoloading {
    z-index: 98;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: black;
}

.player {
    position: relative;
    height: 100%;
    background: black;
}

.timelabel {
    margin-left: 10px;
    color: white;
}

</style>
