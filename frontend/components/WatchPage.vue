<template>
    <div v-if="data">
        <EmbeddedVideo ref="video" width="100%" height="100%" :captionId="firstCaptionId" />
        <div style="display: inline-block; vertical-align: top; max-width: 800px; white-space: normal; word-break: break-all; margin: 30px;">
            <div v-if="data.type === 'movie'"><a :href="youtubeURL(0, 0)">Go</a></div>
            <div
                v-else
                v-for="(season, i) in data.seasons"
            >
                <span>{{ data.seasons.length === 1 ? 'Episodes' : season.name || `Season ${i+1}` }}:</span>
                <br>
                <span style="margin-left: 3px;" v-for="(episode, j) in season.episodes"><a :href="youtubeURL(i, j)" > {{ j + 1 }} </a></span>
            </div>
        </div>
    </div>
</template>

<script>
import EmbeddedVideo from './EmbeddedVideo.vue'

export default {
    components: {
        EmbeddedVideo,
    },
    data: function() { return {
        videoHeight: 0,
    }},
    computed: {
        data: function() {
            return this.$store.state.webWatching;
        },
        firstCaptionId: function() {
            if ([null, undefined].includes(this.data)) return null;
            return this.data.seasons[0].episodes[0].id;
        },
    },
    watch: {
        data: function() {
            this.updateVideoHeight();
        },
    },
    mounted: function() {
        this.updateVideoHeight();
    },
    updated: function() {
        this.updateVideoHeight();
    },
    methods: {
        updateVideoHeight: function() {
            if (
                [null, undefined].includes(this.data) ||
                [null, undefined].includes(this.$refs.video)
            ) {
                return;
            }
            //const width = this.$refs.video.width;
            //const [frameHeight, frameWidth] = this.data.frame_size;
            //this.videoHeight = (width / frameWidth) * frameHeight;
        },
        youtubeURL: function(seasonIdx=null, episodeIdx=null) {
            if ([null, undefined].includes(this.data)) return null;
            seasonIdx = seasonIdx || 0;
            episodeIdx = episodeIdx || 0;
            const playlist = this.data.seasons[seasonIdx].youtube_playlist;
            const captionId = this.data.seasons[seasonIdx].episodes[episodeIdx].id;
            const id = videoIdFromCaptionId(captionId);

            if ([null, undefined].includes(playlist)) {
                return `https://youtube.com/watch?v=${id}`;
            }
            else {
                return `https://youtube.com/watch?v=${id}&list=${playlist}`;
            }
        },
    }
};
</script>

<style>
</style>
