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
