<template>
    <div :class="{ iframecontainer: true, docked: $store.state.captionDocked }">
        <div ref="videocontainer" class="videocontainer">
            <div v-show="!playerReady" class="videoloading" />
            <div v-if="$store.state.isMovingCaption && !$store.state.isLocal" class="dragsurface" />
            <div :ref="playerId" :id="playerId" class="player">
                <div v-if="$store.state.isLocal" style="position: absolute; bottom: 0; left: 0; right: 0;">
                    <div style="margin-left: 20%">
                        <q-slider vertical-middle style="width: 80%" color="red" dark v-model="mockTime" :min="0" :max="videoDuration" :step="0.5" />
                        <q-btn vertical-middle dark color="red" v-if="mockPlaying" label="Pause" @click="setMockPlaying(false)" />
                        <q-btn vertical-middle dark color="green" v-else label="Play" @click="setMockPlaying(true)"/>
                        <span class="timelabel">{{currentTimeLabel()}}</span>
                    </div>
                </div>
            </div>
        </div>
        <EmbeddedCaption
            class="embeddedcaption"
            ref="embeddedcaption"
            v-show="playerReady"
            v-bind:playerId="playerId"
        />
    </div>
</template>

<script>
import EmbeddedCaption from './EmbeddedCaption.vue'

const MOCK_CLOCK_SPEED = 0.01; // s
let lastT = null;

export default {
    mixins: [mixin],
    props: ['playerId', 'width', 'height'],
    components: {
        EmbeddedCaption,
    },
    data: function() {
        return {
            uuid: null,
            initializing: false,
            playerReadyCaptionId: false,
            focusInterval: null,
            // Mock variables are used if LOCAL is true (i.e. no youtube available)
            mockPlaying: false,
            mockTime: 0.0,
            resizeObserver: null,
        };
    },
    mounted: function(){
        const self = this;
        this.uuid = uuidv4();
        this.initYoutube();
        // If the video iframe gets focus, we keyboard shortcuts stop working, so we need to refocus the caption
        this.focusInterval = setInterval(function() {
            if (document.activeElement.tagName === 'IFRAME' && self.videoAPI && ! self.videoAPI.isPaused()) {
                focus(self.$refs.embeddedcaption);
            }
        }, 100);

        if (LOCAL) {
            this.sustitueClock = setInterval(function() {
                if (self.mockPlaying) {
                    self.mockTime += MOCK_CLOCK_SPEED;
                    if (self.mockTime > self.videoDuration) {
                        self.mockTime = self.videoDuration;
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
    },
    beforeUnmount: function() {
        this.destroyYoutube();
        clearInterval(this.focusInterval);
        this.focusInterval = null;
        this.resizeObserver.disconnect();
    },
    watch: {
        navigateToCaptionIdxKey: function() {
            if (! this.playerReady || isNone(this.captionData) || isNone(this.navigateToCaptionIdx) || isNone(this.videoAPI)) {
                return;
            }

            const line = captionArrayToDict(this.captionData.lines, this.navigateToCaptionIdx, this.captionData);
            console.log('Setting videoAPI time', this.captionData.lines, line.t0, this.navigateToCaptionIdx, line);
            this.$store.commit('setPlayerData', {playerId: this.playerId, navigateToCaptionIdx: null});
            this.videoAPI.setCurrentTime(line.t0 + 0.001);
            const self = this;
            const setCurrentTimeInterval = setInterval(function() {
                if (self.videoAPI.getCurrentTime() - line.t0 + 0.001 < 0.01) {
                    clearInterval(setCurrentTimeInterval);
                }
                else {
                    self.videoAPI.setCurrentTime(line.t0 + 0.001);
                }
            }, 100);
        },
        playerReadyCaptionId: function() {
            if (!this.playerReadyCaptionId) return;
            if (this.$refs.embeddedcaption && this.$refs.embeddedcaption.$el) {
                this.resizeObserver.observe(this.$refs.embeddedcaption.$el);
            }
        },
        captionId: function() {
            if (this.initializing || this.playerReady) return;
            if (this.playerReadyCaptionId) this.destroyYoutube();
            this.initYoutube();
        },
    },
    computed: {
        playerReady: function() {
            return this.playerReadyCaptionId && this.playerReadyCaptionId === this.captionId;
        },
        navigateToCaptionIdxKey: function() {
            return `${this.playerReadyCaptionId}|${this.navigateToCaptionIdx}|${this.captionData}|${this.videoAPI}`;
        },
        youtubeAPIReady: function() {
            return this.$store.state.youtubeAPIReady;
        },
        captionDuration: function() {
            if (isNone(this.captionData)) return 0;
            return this.captionData.video_length;
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
            this.playerReadyCaptionId = false;
            this.mockTime = 0;
            this.mockPlaying = false;
        },
        initYoutube: function() {
            const self = this;
            if (! this.$store.state.youtubeAPIReady || ! this.captionId || this.playerReady || this.initializing) return;

            if (! LOCAL) {
                this.initializing = true;
                this.$nextTick(() => { // nextTick because player element may not be done
                    console.log('initing initYoutube', this.uuid, this.playerId, this.captionId, document.querySelectorAll('#' + this.playerId));
                    this.player = new YT.Player(this.playerId, {
                        width: this.width,
                        height: this.height,
                        videoId: videoIdFromCaptionId(this.captionId),
                        playerVars: {
                            'playsinline': 1,
                            'rel': 0,
                            'cc_load_policy': 0,
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
            this.$store.commit('setPlayerData', {playerId: this.playerId, videoAPI: videoAPI});
            if (LOCAL) {
                this.onReady();
            }
        },
        onReady: function() {
            let $el = document.getElementById(this.playerId);
            this.$store.commit('setPlayerData', {playerId: this.playerId, AVElement: $el});
            this.$store.commit('setPlayerData', {playerId: this.playerId, videoDuration: this.getDuration()});
            const self = this;
            // Wait a bit before setting playerReadyCaptionId to remove flickering because iframe hasn't fully rendered yet
            setTimeout((function(captionId) { return function() {
                console.log('playerReadyCaptionId', self.playerId);
                self.playerReadyCaptionId = captionId;
                self.initializing = false;
            }})(this.captionId), 100);
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
            if (LOCAL) return this.videoDuration; // we have no youtube iframe, so use the time we get from caption data
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
            if ([null, undefined].includes(this.AVElement)) return;
            if (event.data === YT.PlayerState.PLAYING) {
                this.AVElement.dispatchEvent(new Event('play'));
            }
            else if (event.data === YT.PlayerState.PAUSED) {
                this.AVElement.dispatchEvent(new Event('pause'));
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
