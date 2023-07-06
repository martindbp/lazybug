<template>
    <div ref="reviewpage" v-if="reviewCaptionId" style="position: relative">
        <EmbeddedVideo
            ref="reviewvideo"
            playerId="review"
            width="100%"
            height="100%"
            v-bind:reviewCaptionIndices="reviewCaptionIndices"
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
        hidden: false,
        reviewCaptionId: null,
        reviewCaptionIndices: [],
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
    },
    watch: {
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
            this.reviewCaptionIndices = this.captionIdIndices[this.reviewCaptionId].sort(function(a, b) {
              return a - b;
            });
            this.$store.commit('setCaptionId', {playerId: 'review', value: this.reviewCaptionId});
            this.$store.commit('setPlayerData', {
                playerId: 'review',
                navigateToCaptionIdx: this.captionIdIndices[this.reviewCaptionId][0],
            });
        },
    },
    methods: {
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
                            if (self.submittedExercises && self.submittedExercises[captionIdx]) continue; // already did this session
                            if (! isStarredWordActive(states, hz, pys, tr, threshold)) continue;

                            const stateKey = getStateKey('word', hz, pys, tr, null);
                            if (seenStateKeys.has(stateKey)) continue;
                            seenStateKeys.add(stateKey);

                            captions.push(row.captionId);
                            if (! exercises[row.captionId]) exercises[row.captionId] = [];
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
