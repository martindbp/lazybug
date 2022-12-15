<template>
    <div ref="playerpage" v-if="showInfo" style="position: relative">
        <EmbeddedVideo ref="video" width="100%" height="100%" :captionId="captionId" />
        <VideoPicker :hidden="hidden" />
    </div>
</template>

<script>
import EmbeddedVideo from './EmbeddedVideo.vue'
import VideoPicker from './VideoPicker.vue'

export default {
    mixins: [mixin],
    components: {
        EmbeddedVideo,
        VideoPicker,
    },
    data: function() { return {
        hidden: false,
    }},
    updated: function() {
        if (this.$refs.playerpage) {
            this.hidden = this.$refs.playerpage.style.display === 'none';
            if (this.hidden) {
                // If we navigated away from watch page, we should pause the video
                this.$refs.video.pause();
            }
        }
    },
};
</script>

<style>
.episodeselector .q-fab__actions {
    flex-wrap: wrap !important;
    justify-content: left !important;
    min-width: 700px;
}

.mobile .episodeselector .q-fab__actions {
    min-width: 300px;
    -webkit-overflow-scrolling: touch;
    will-change: scroll-position;
    overflow: auto;
    height: 500px;
}

.episodeselector .q-fab__actions .q-btn {
    font-size: 10px !important;
}

.videopicker {
    position: absolute;
    left: 5px;
    top: 185px;
}

.videopicker.mobile {
    top: 15px;
}
</style>
