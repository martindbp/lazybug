<template>
    <div class="dark" v-if="$store.state.youtubeAPIReady">
        <div id="player" />
        <div id="lazybugroot" class="lazybug"> <!-- to mimic the browser extension mount -->
            <Caption
                v-if="captionId"
                v-bind:captionId="captionId"
                v-bind:AVElement="AVElement"
                v-bind:videoDuration="videoDuration"
                v-bind:videoAPI="videoAPI"
            />
        </div>
    </div>
</template>

<script>
import Caption from './Caption.vue'

let player = null; // the Youtube iframe API player singleton

export default {
    components: {
        Caption,
    },
    props: ['captionId'],
    data: function() {
        return {
            player: null,
            playerReady: false,
        };
    },
    computed: {
        videoId: function() {
            return videoIdFromCaptionId(this.captionId);
        },
        videoAPI: function() {
            return  {
                getCurrentTime: this.getCurrentTime,
                setCurrentTime: this.setCurrentTime,
                getDuration: this.getDuration,
                play: this.play,
                pause: this.pause,
                isPaused: this.isPaused,
            }
        },
    },
    mounted: function(){
        const self = this;
        this.player = new YT.Player('player', {
            height: '390',
            width: '640',
            videoId: this.videoId,
            playerVars: {
                'playsinline': 1,
                'rel': 0,
            },
            events: {
                'onReady': function() { self.playerReady = true; },
                'onStateChange': this.onPlayerStateChange
            }
        });
    },
    methods: {
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
            if ([null, undefined].includes(this.AVElement)) return;
            if (event.data === YT.PlayerState.PLAYING) {
                this.AVElement.dispatchEvent(new Event('play'));
            }
            else if (event.data === YT.PlayerState.PAUSED) {
                this.AVElement.dispatchEvent(new Event('stop'));
            }
        },
    },
};
</script>

<style>
</style>
