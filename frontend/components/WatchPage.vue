<template>
    <div ref="watchpage" v-if="showInfo" style="position: relative">
        <EmbeddedVideo ref="video" width="100%" height="100%" :captionId="captionId" />
        <div v-if="showInfo.type !== 'movie'" style="position: absolute; left: 5px; top: 185px;">
            <div style="margin-bottom: 15px">
                <q-fab
                    :label="getSeasonName(season)"
                    color="blue"
                    icon="keyboard_arrow_right"
                    direction="right"
                    padding="xs"
                >
                    <q-fab-action v-for="(s, i) in showInfo.seasons" color="blue" :label="getSeasonName(i)" @click="season = i" />
                </q-fab>
            </div>
            <div>
                <q-fab
                    class="videoselector"
                    :label="getEpisodeName(episode)"
                    color="deep-orange"
                    icon="keyboard_arrow_right"
                    direction="right"
                    padding="xs"
                >
                    <q-fab-action color="deep-orange" paddings="xs" v-for="(e, i) in showInfo.seasons[season].episodes" :label="i+1" @click="episode = i" />
                </q-fab>
            </div>
        </div>
        <q-page-sticky position="bottom-center" :offset="[0, -3]">
            <q-btn fab icon="keyboard_arrow_up" color="primary" glossy />
        </q-page-sticky>
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
        showInfo: function() {
            return this.$store.state.watchingShowInfo;
        },
        season: {
            get: function() { return this.$store.state.watchingSeason; },
            set: function(val) { this.$store.commit('setWatchingSeason', val); },
        },
        episode: {
            get: function() { return this.$store.state.watchingEpisode; },
            set: function(val) { this.$store.commit('setWatchingEpisode', val); },
        },
        captionId: function() {
            if ([null, undefined].includes(this.showInfo)) return null;
            return this.showInfo.seasons[this.season].episodes[this.episode].id;
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
        if (this.$refs.watchpage && this.$refs.watchpage.style.display === 'none') {
            // If we navigated away from watch page, we should pause the video
            this.$refs.video.pause();
        }
        this.updateVideoHeight();
    },
    methods: {
        getSeasonName: function(i) {
            return getSeasonName(this.showInfo, i);
        },
        getEpisodeName: function(i) {
            return getEpisodeName(this.showInfo, this.season, i);
        },
        updateVideoHeight: function() {
            if (
                [null, undefined].includes(this.showInfo) ||
                [null, undefined].includes(this.$refs.video)
            ) {
                return;
            }
            //const width = this.$refs.video.width;
            //const [frameHeight, frameWidth] = this.showInfo.frame_size;
            //this.videoHeight = (width / frameWidth) * frameHeight;
        },
        youtubeURL: function(seasonIdx=null, episodeIdx=null) {
            if ([null, undefined].includes(this.showInfo)) return null;
            seasonIdx = seasonIdx || 0;
            episodeIdx = episodeIdx || 0;
            const playlist = this.showInfo.seasons[seasonIdx].youtube_playlist;
            const captionId = this.showInfo.seasons[seasonIdx].episodes[episodeIdx].id;
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
.videoselector .q-fab__actions {
    flex-wrap: wrap !important;
    justify-content: left !important;
    min-width: 700px;
}

.videoselector .q-fab__actions .q-btn {
    font-size: 10px !important;
}

</style>
