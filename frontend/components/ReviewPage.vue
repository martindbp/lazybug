<template>
    <div class="noreviews" v-if="! isLoading && currentReviewCaptionIdx === null">
        <q-dialog seamless v-model="showDone">
            <q-card>
                <q-card-section>
                    <div class="text-h5">All Done</div>
                </q-card-section>

                <q-card-section class="q-pt-none text-h6">
                    There are no more videos to review for now, check back after you've watched more videos!
                </q-card-section>
            </q-card>
        </q-dialog>
    </div>
    <div ref="reviewpage" v-else-if="reviewCaptionId" style="position: relative">
        <q-carousel
            v-if="currentReviewCaptionIdx !== null"
            dark
            class="reviewpicker shadow-1 rounded-borders"
            v-model="currentReviewCaptionIdx"
            transition-prev="scale"
            transition-next="scale"
            swipeable
            animated
            padding
            arrows
         >
             <q-carousel-slide v-for="(captionId, i) in reviewCaptionsList" :name="i" class="column no-wrap flex-center">
                 <div class="text-h6 text-center">
                     {{ captionTitle }}
                 </div>
             </q-carousel-slide>
        </q-carousel>
        <EmbeddedVideo
            v-if="! isLoading && currentReviewCaptionIdx !== null"
            ref="reviewvideo"
            playerId="review"
            width="100%"
            height="100%"
        />
    </div>
</template>

<script>
import EmbeddedVideo from './EmbeddedVideo.vue'

export default {
    mixins: [mixin],
    components: {
        EmbeddedVideo,
    },
    data: function() { return {
        playerId: 'review',
        hidden: false,
        showDone: true,
        reviewCaptionId: null,
        currentReviewCaptionIdx: null,
    }},
    mounted: function() {
        this.updateExercises();
    },
    updated: function() {
        if (this.$refs.reviewpage) {
            this.hidden = this.$refs.reviewpage.style.display === 'none';
            if (this.hidden) {
                // If we navigated away from watch page, we should pause the video
                this.$refs.reviewvideo.pause();
            }
        }
    },
    computed: {
        showList: function() {
            return this.$store.state.showList;
        },
        captionTitle: function() {
            if (isNone(this.showInfo) || isNone(this.season) || isNone(this.episode)) return '';
            if (this.showInfo.type !== 'tv') {
                return resolveShowName(this.showInfo.name);
            }
            const captionStr = `${resolveShowName(this.showInfo.name)} - ${getSeasonName(this.showInfo, this.season)} - ${getEpisodeName(this.showInfo, this.season, this.episode)}`;

            const idxStr = `${this.currentCaptionIdx + 1}/${this.captionData.lines.length}`;
            return `${captionStr} - ${idxStr}`;
        },
        reviewCaptionsList: function() {
            return this.$store.state.reviewCaptionsList;
        },
        reviewCaptionIdIndices: function() {
            return this.$store.state.reviewCaptionIdIndices;
        },
    },
    watch: {
        AVElement: {
            immediate: true,
            handler: function(newValue, oldValue) {
                if (! newValue) return;
                const self = this;
                newValue.addEventListener('nextVideo', function() {
                    self.onNextVideo();
                });
            },
        },
        showList: {
            immediate: true,
            handler: function(newData) {
                if (! newData) return;
                this.updateExercises();
            },
        },
        currentReviewCaptionIdx: function() {
            if (this.currentReviewCaptionIdx === null) return;
            this.reviewCaptionId = this.reviewCaptionsList[this.currentReviewCaptionIdx];
            const reviewCaptionIndices = this.reviewCaptionIdIndices[this.reviewCaptionId].sort(function(a, b) {
              return a - b;
            });
            this.$store.commit('resetPlayerData', 'review');
            this.$store.commit('setCaptionId', {playerId: 'review', value: this.reviewCaptionId});
            this.$store.commit('setPlayerData', {
                playerId: 'review',
                navigateToCaptionIdx: 0,
                reviewCaptionIndices: reviewCaptionIndices,
            });
        },
    },
    methods: {
        onNextVideo: function() {
            if (this.currentReviewCaptionIdx === null) return;
            if (this.currentReviewCaptionIdx === this.reviewCaptionsList.length - 1) {
                this.currentReviewCaptionIdx = null;
            }
            else {
                this.currentReviewCaptionIdx = (this.currentReviewCaptionIdx + 1) % this.reviewCaptionsList.length;
            }
        },
    },
};
</script>
<style>
.reviewpicker {
    position: fixed !important;
    top: 0 !important;
    height: 70px !important;
    width: 25vw;
    z-index: 999;
    left: 50%;
    transform: translate(-50%, -0%);
    color: #fff;
    background: var(--q-dark) !important;
}

.noreviews {
    z-index: 98;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: black;
}
</style>
