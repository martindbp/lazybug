<template>
    <div v-if="$store.state.youtubeAPIReady">
        <div id="player" />
        <Caption
            v-if="captionId"
            v-bind:captionId="captionId"
            v-bind:AVElement="AVElement"
            v-bind:videoDuration="videoDuration"
            v-bind:videoAPI="videoAPI"
        />
    </div>
</template>

<script>
import Caption from './Caption.vue'

export default {
    components: {
        Caption,
    },
    props: ['captionId'],
    data: function() {
        return {
            player: null,
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
        this.player = new YT.Player('player', {
            height: '390',
            width: '640',
            videoId: this.videoId,
            playerVars: {
                'playsinline': 1,
                'rel': 0,
            },
            events: {
                //'onReady': onPlayerReady,
                'onStateChange': this.onPlayerStateChange
            }
        });
    },
    beforeDestroy: function() {
    },
    methods: {
        getCurrentTime: function() {
            return this.player.getCurrentTime();
        },
        setCurrentTime: function(t) {
            this.player.seekTo(t, true); // allowSeekAhead
        },
        getDuration: function() {
            return this.player.getDuration();
        },
        play: function() {
            this.player.playVideo();
        },
        pause: function() {
            this.player.pauseVideo();
        },
        isPaused: function() {
            return this.player.getPlayerState() === 2;
        },
        onPlayerStateChange: function(event) {
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
