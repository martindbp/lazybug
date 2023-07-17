<template>
    <div ref="reviewpage" v-if="reviewCaptionId" style="position: relative">
        <q-carousel
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
             <q-carousel-slide v-for="(captionId, i) in captionsList" :name="i" class="column no-wrap flex-center">
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
        <div v-if="! isLoading && currentReviewCaptionIdx === null">
            No reviews to be done
        </div>
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
        isLoading: true,
        hidden: false,
        reviewCaptionId: null,
        currentReviewCaptionIdx: null,
        captionsList: [],
        captionIdIndices: {},
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
            return `${resolveShowName(this.showInfo.name)} - ${getSeasonName(this.showInfo, this.season)} - ${getEpisodeName(this.showInfo, this.season, this.episode)}`;
        },
    },
    watch: {
        AVElement: {
            immediate: true,
            handler: function(newValue, oldValue) {
                if (! newValue) return;
                const self = this;
                console.log('Listening to ', newValue);
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
            this.reviewCaptionId = this.captionsList[this.currentReviewCaptionIdx];
            const reviewCaptionIndices = this.captionIdIndices[this.reviewCaptionId].sort(function(a, b) {
              return a - b;
            });
            console.log('new currentReviewCaptionIdx', this.currentReviewCaptionIdx);
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
            const self = this;
            self.currentReviewCaptionIdx = (self.currentReviewCaptionIdx + 1) % self.captionsList.length;
            console.log('new currentReviewCaptionIdx', self.currentReviewCaptionIdx);
        },
        updateExercises: function() {
            // 1. Go through event log, find answered exercises
            // 2. Check if they're still active and haven't been answered this session
            // 3. Collect them, group them by word, select one caption per word randomly
            // 4. Now we have a list of captionId and captionIdx, sort by answer date

            if (this.showList === null) return;

            const self = this;
            const fromEventId = getEvent('answer', 'py');
            const toEventId = getEvent('answer', 'tr');
            const states = this.$store.state.states;
            const threshold = this.$store.state.options.exercisesKnownThreshold;

            getAnswerHistory(function(data) {
                const exercises = {};
                const captions = [];
                const seenStateKeys = new Set();
                data = data.filter((row) => row.seasonIdx !== null);  // bogus data that was probably added because of a bug
                for (const row of data) {
                    const showId = row.showId;
                    row.showInfo = self.showList[showId];
                    if (!row.showInfo) continue;

                    for (let i = 0; i < row.eventIds.length; i++) { 
                        if (row.eventIds[i] >= fromEventId && row.eventIds[i] <= toEventId) {
                            if (row.eventData[i].length != 6) continue;
                            const [hz, pys, tr, correct, captionIdx, answer] = row.eventData[i];
                            //if (self.submittedExercises && self.submittedExercises[captionIdx]) continue; // already did this session
                            if (! isStarredWordActive(states, hz, pys, tr, threshold)) continue;

                            const stateKey = getStateKey('word', hz, pys, tr, null);
                            if (seenStateKeys.has(stateKey)) continue;
                            seenStateKeys.add(stateKey);

                            if (! exercises[row.captionId]) {
                                captions.push(row.captionId);
                                exercises[row.captionId] = [];
                            }
                            exercises[row.captionId].push(captionIdx);
                        }
                    }
                }

                self.captionsList = captions;
                self.captionIdIndices = exercises;
                if (captions.length > 0) {
                    self.currentReviewCaptionIdx = 0;
                }
                else {
                    self.currentReviewCaptionIdx = null;
                }

                self.isLoading = false;
            });
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
</style>
