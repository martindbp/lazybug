<template>
    <div ref="playerpage" v-if="showInfo" style="position: relative">
        <EmbeddedVideo ref="video" width="100%" height="100%" :captionId="captionId" />
        <div v-if="showInfo.type !== 'movie'" style="position: absolute; left: 5px; top: 185px;">
            <div style="margin-bottom: 15px">
                <q-fab
                    ref="seasonselector"
                    :label="getSeasonName(season)"
                    color="blue"
                    icon="keyboard_arrow_right"
                    direction="right"
                    padding="xs"
                >
                    <q-fab-action
                        v-for="(s, i) in showInfo.seasons"
                        color="blue"
                        :label="getSeasonName(i)"
                        @click.stop.prevent="season = i; $refs.episodeselector.show()"
                    />
                </q-fab>
            </div>
            <div>
                <q-fab
                    ref="episodeselector"
                    class="episodeselector"
                    :label="getEpisodeName(episode)"
                    color="green"
                    icon="keyboard_arrow_right"
                    @click="$refs.seasonselector.hide()"
                    direction="right"
                    padding="xs"
                >
                    <q-fab-action
                        v-for="(e, i) in showInfo.seasons[season].episodes"
                        :color="e.processed ? 'green' : 'red'"
                        paddings="xs"
                        :label="i+1"
                        @click.stop.prevent="episode = i;"
                    />
                </q-fab>
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
        clickEventListener: null,
        hidden: false,
    }},
    computed: {
        showInfo: function() {
            return this.$store.state.playerShowInfo;
        },
        season: {
            get: function() { return this.$store.state.playingSeason; },
            set: function(val) { this.$store.commit('setPlayingSeason', val); },
        },
        episode: {
            get: function() { return this.$store.state.playingEpisode; },
            set: function(val) { this.$store.commit('setPlayingEpisode', val); },
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
        const self = this;
        this.updateVideoHeight();
        this.clickEventListener = document.addEventListener('click', function(evt) {
            if (self.hidden || evt.target.closest('.q-fab')) return;
            self.$refs.seasonselector.hide();
            self.$refs.episodeselector.hide();
        });
    },
    unmounted: function() {
        document.removeEventListener(this.clickEventListener);
        this.clickEventListener = null;
    },
    updated: function() {
        if (this.$refs.playerpage) {
            this.hidden = this.$refs.playerpage.style.display === 'none';
            if (this.hidden) {
                // If we navigated away from watch page, we should pause the video
                this.$refs.video.pause();
            }
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
.episodeselector .q-fab__actions {
    flex-wrap: wrap !important;
    justify-content: left !important;
    min-width: 700px;
}

.episodeselector .q-fab__actions .q-btn {
    font-size: 10px !important;
}

</style>
