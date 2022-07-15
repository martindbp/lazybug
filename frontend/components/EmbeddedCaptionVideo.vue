<template>
    <div v-if="$store.state.youtubeAPIReady">
        <div id="player" />
        <Caption
            v-if="captionId"
            embedded="false"
            v-bind:captionId="captionId"
            v-bind:AVElement="AVElement"
            v-bind:videoDuration="videoDuration"
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
        }
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
                //'onStateChange': onPlayerStateChange
            }
        });
    },
    beforeDestroy: function() {
    },
    methods: {
        getCurrentTime: function() {

        },
        setCurrentTime: function(t) {

        },
    },
};
</script>

<style>
</style>
