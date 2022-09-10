<template>
    <div class="iframecontainer">
        <div v-show="!playerReady" class="videoloading" />
        <div v-if="$store.state.isMovingCaption && !localOnly" class="dragsurface" />
        <div ref="player" :id="playerID" class="player">
            <div style="position: absolute; bottom: 0; left: 0; right: 0;" v-if="localOnly" >
                <q-btn vertical-middle dark color="red" v-if="substitutePlaying" label="Pause" @click="setSubstitutePlaying(false)" />
                <q-btn vertical-middle dark color="green" v-else label="Play" @click="setSubstitutePlaying(true)"/>
                <q-slider vertical-middle style="display: inline-block; width: 80%" color="red" dark v-model="substituteTime" :min="0" :max="captionDuration" :step="0.5" />
                <span>{{currentTimeLabel()}}</span>
            </div>
        </div>
        <EmbeddedCaption ref="embeddedcaption" v-show="playerReady" />
    </div>
</template>

<script>
import EmbeddedCaption from './EmbeddedCaption.vue'

const SUBSTITUTE_CLOCK_SPEED = 0.01; // s

export default {
    props: ['captionId', 'width', 'height'],
    components: {
        EmbeddedCaption,
    },
    data: function() {
        return {
            playerID: uuidv4(),
            player: null,
            playerReady: false,
            focusInterval: null,
            localOnly: LOCAL_ONLY,
            // Substitute variables are used if LOCAL_ONLY is true (i.e. no youtube available)
            substitutePlaying: false,
            substituteTime: 0.0,
        };
    },
    mounted: function(){
        this.initYoutube();
        const self = this;
        // If the video iframe gets focus, we keyboard shortcuts stop working, so we need to refocus the caption
        this.focusInterval = setInterval(function() {
            if (document.activeElement.tagName === 'IFRAME') {
                focus(self.$refs.embeddedcaption);
            }
        }, 100);

        if (LOCAL_ONLY) {
            this.sustitueClock = setInterval(function() {
                if (self.substitutePlaying) {
                    self.substituteTime += SUBSTITUTE_CLOCK_SPEED;
                    if (self.substituteTime > self.captionDuration) {
                        self.substituteTime = self.captionDuration;
                        self.substitutePlaying = false;
                    }
                }
            }, SUBSTITUTE_CLOCK_SPEED * 1000);
        }
    },
    beforeUnmount: function() {
        this.destroyYoutube();
        clearInterval(this.focusInterval);
        this.focusInterval = null;
    },
    watch: {
        captionId: function() {
            this.destroyYoutube();
            this.initYoutube();
        },
    },
    computed: {
        captionDuration: function() {
            if (this.$store.state.captionData === null) return 0;
            return this.$store.state.captionData.video_length;
        }
    },
    methods: {
        currentTimeLabel: function() {
            return '';
            //const h = Math.floor(this.getCurrentTime());
            //const m = Math.floor(this.getCurrentTime());
            //const s = 
        },
        setSubstitutePlaying: function(playing) {
            this.substitutePlaying = playing;
            this.onPlayerStateChange({data: playing ? YT.PlayerState.PLAYING : YT.PlayerState.PAUSED});
        },
        destroyYoutube: function() {
            if (this.player && ! LOCAL_ONLY) {
                this.player.destroy();
                this.player = null;
            }
            this.playerReady = false;
            this.substituteTime = 0;
            this.substitutePlaying = false;
        },
        initYoutube: function() {
            const self = this;
            if (! LOCAL_ONLY) {
                this.player = new YT.Player(this.playerID, {
                    width: this.width,
                    height: this.height,
                    videoId: videoIdFromCaptionId(this.captionId),
                    playerVars: {
                        'playsinline': 1,
                        'rel': 0,
                        'autoplay': 1,
                    },
                    events: {
                        'onReady': self.onReady,
                        'onStateChange': this.onPlayerStateChange
                    }
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
            if (LOCAL_ONLY) {
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
                self.playerReady = true;
            }, 100);
        },
        getCurrentTime: function() {
            if (! this.playerReady) return 0;
            if (LOCAL_ONLY) return this.substituteTime;
            return this.player.getCurrentTime();
        },
        setCurrentTime: function(t) {
            if (! this.playerReady) return;
            if (LOCAL_ONLY) {
                this.substituteTime = Math.floor(t);
                return;
            }
            this.player.seekTo(t, true); // allowSeekAhead
        },
        getDuration: function() {
            if (! this.playerReady) return 0;
            if (LOCAL_ONLY) return this.captionDuration(); // we have no youtube iframe, so use the time we get from caption data
            return this.player.getDuration();
        },
        play: function() {
            if (! this.playerReady) return;
            if (LOCAL_ONLY) {
                this.setSubstitutePlaying(true);
                return;
            }
            this.player.playVideo();
        },
        pause: function() {
            if (! this.playerReady) return;
            if (LOCAL_ONLY) {
                this.setSubstitutePlaying(false);
                return;
            }
            this.player.pauseVideo();
        },
        isPaused: function() {
            if (! this.playerReady) return false;
            if (LOCAL_ONLY) return !this.substitutePlaying;
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
    height: 100%;
    background: black;
}
</style>
