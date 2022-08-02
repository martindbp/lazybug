<template>
    <div class="iframecontainer">
        <div v-if="$store.state.isMovingCaption" class="dragsurface" />
        <div ref="player" :id="playerID" />
        <EmbeddedCaption />
    </div>
</template>

<script>
import EmbeddedCaption from './EmbeddedCaption.vue'

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
        };
    },
    mounted: function(){
        const self = this;
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
    },
    methods: {
        onReady: function() {
            this.playerReady = true;
            let $el = document.getElementById(this.playerID);
            this.$store.commit('setAVElement', $el);
            this.$store.commit('setVideoDuration', this.getDuration());
        },
        getCurrentTime: function() {
            if (! this.playerReady) return 0;
            return this.player.getCurrentTime();
        },
        setCurrentTime: function(t) {
            if (! this.playerReady) return;
            this.player.seekTo(t, true); // allowSeekAhead
        },
        getDuration: function() {
            if (! this.playerReady) return 0;
            return this.player.getDuration();
        },
        play: function() {
            if (! this.playerReady) return;
            this.player.playVideo();
        },
        pause: function() {
            if (! this.playerReady) return;
            this.player.pauseVideo();
        },
        isPaused: function() {
            if (! this.playerReady) return false;
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
</style>
