<template>
    <div class="noreviews" v-if="! userHasStarredAtLeastOneWord">
        <q-dialog seamless v-model="showNoReviews">
            <q-card>
                <q-card-section class="row items-center">
                    <q-avatar icon="error" color="orange" text-color="white" />
                    <span class="q-ml-lg">Nothing To Review</span>
                </q-card-section>
                <q-card-section >
                    <div>
                        There are no starred words yet, star a word like this (and do the exercise)
                        <video autoplay loop style="width: 100%">
                            <source src="https://cdn.lazybug.ai/file/lazybug-public/images/starringword.webm" type="video/webm">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    <q-btn class="q-mt-md" color="green" label="Take me to the content" @click="clickPage('content')" />
                </q-card-section>
            </q-card>
        </q-dialog>
    </div>
    <div class="noreviews" v-else-if="! isLoading && currentReviewCaptionIdx === null">
        <q-dialog seamless v-model="showDone">
            <q-card>
                <q-card-section class="row items-center">
                    <q-avatar icon="done" color="green" text-color="white" />
                    <span class="q-ml-lg">All Done</span>
                </q-card-section>
                <q-card-section >
                    <div>
                        There are no more videos to review for now, check back after you've watched more videos!
                    </div>
                    <q-btn color="green" label="Take me to the content" @click="clickPage('content')" />
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
        isLoading: true,
        playerId: 'review',
        hidden: false,
        showDone: true,
        showNoReviews: true,
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
        userHasStarredAtLeastOneWord: function() {
            for (const key of Object.keys(this.$store.state.states)) {
                const state = getState(this.$store.state.states, key, StateStarred, StateNone);
                if (state === StateStarred) return true;
            }
            return false;
        },
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
            this.isLoading = false;
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
