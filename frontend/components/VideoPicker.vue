<template>
    <div v-if="showInfo" :class="{videopicker: true, mobile: isMobile, extension: isExtension}">
        <div v-if="!isMovie && hasMultipleSeasons" style="margin-bottom: 15px">
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
        <div v-if="!isMovie" style="margin-bottom: 15px">
            <q-fab
                ref="episodeselector"
                class="episodeselector"
                :label="getEpisodeName(episode)"
                color="green"
                icon="keyboard_arrow_right"
                @click="$refs.seasonselector ? $refs.seasonselector.hide() : null"
                direction="right"
                padding="xs"
            >
                <q-fab-action
                    v-for="(e, i) in showInfo.seasons[season].episodes"
                    :color="e.processed ? 'green' : 'red'"
                    paddings="xs"
                    :label="i+1"
                    @click.stop.prevent="playEpisode(i)"
                />
            </q-fab>
        </div>
        <div v-if="$store.state.playingCaptionIdx !== null">
            <q-fab
                ref="commentselector"
                class="commentselector"
                icon="chat"
                color="secondary"
                vertical-actions-align="left"
                :label="numComments > 0 ? numComments : ''"
                @click.stop.prevent="clickComments()"
                direction="down"
                padding="s"
            >
                <q-fab-action
                    v-for="comment in captionComments"
                    class="comment"
                    color="primary"
                    paddings="xs"
                    @click.stop.prevent="showComment(comment)"
                >
                    <span class="innercomment" v-html="`@${comment.username}: ${comment.cooked}`" />
                </q-fab-action>
                <q-fab-action
                    color="secondary"
                    paddings="xs"
                    label="Comment"
                    @click.stop.prevent="askQuestion()"
                />
            </q-fab>
        </div>
        <CommentsDialog :comments="captionComments" />
    </div>
</template>

<script>
import CommentsDialog from './CommentsDialog.vue'

export default {
    mixins: [mixin],
    props: {
        hidden: { default: false },
    },
    components: {
        CommentsDialog
    },
    data: function() { return {
        clickEventListener: null,
        commentsAreOpen: false,
        manuallyClosedComments: false,
    }},
    computed: {
        needLogin: function() {
            return [null, undefined].includes(this.$store.state.accountEmail) || this.numComments === null;
        },
        hasMultipleSeasons: function() {
            if (this.showInfo) return this.showInfo.seasons.length > 1;
            else return false;
        },
        isMovie: function() {
            return this.showInfo && this.showInfo.type === 'movie';
        },
        numComments: function() {
            return Array.isArray(this.captionComments) ? this.captionComments.length : null;
        },
        baseDiscourseURL: function() {
            const topicSlug = this.showInfo.discourse_topic_slug;
            const topicId = this.showInfo.discourse_topic_id;
            return `https://discourse.lazybug.ai/t/${topicSlug}/${topicId}`;
        }
    },
    mounted: function() {
        const self = this;
        this.clickEventListener = document.addEventListener('click', function(evt) {
            if (self.hidden || evt.target.closest('.q-fab')) return;
            if (self.$refs.seasonselector) self.$refs.seasonselector.hide();
            if (self.$refs.episodeselector) self.$refs.episodeselector.hide();
        });
    },
    unmounted: function() {
        document.removeEventListener(this.clickEventListener);
        this.clickEventListener = null;
    },
    updated: function() {
        // The comments come with "<blockquote>"'s which we want to remove. Instead of cooking up some
        // complex regex and remove it from the "cooked" comment string, we let the HTML render and then
        // remove the blockquote nodes
        // Then remove other tags like <p> by setting innerHTML = innerText
        const self = this;
        this.$nextTick(function () {
            for (const node of document.querySelectorAll('.comment blockquote')) {
                node.remove();
            }

            for (const node of document.querySelectorAll('.innercomment')) {
                node.innerHTML = node.innerText;
            }

        });
    },
    watch: {
        numComments: {
            immediate: true,
            handler: function() {
                // Open the comments once if there are comments, but after that it remains closed if user closes it
                if (! this.$refs.commentselector || this.numComments === null) return;

                if (this.commentsAreOpen && this.numComments === 0) {
                    this.$refs.commentselector.hide();
                    this.commentsAreOpen = false;
                }
                else if (!this.commentsAreOpen && this.numComments > 0 && ! this.manuallyClosedComments) {
                    this.$refs.commentselector.show();
                    this.commentsAreOpen = true;
                }
            },
        }
    },
    methods: {
        playEpisode: function(i) {
            this.setPlaying(this.showInfo.showId, this.$store.state.playingSeason, i);
        },
        goDiscourse: function() {
            window.open(this.baseDiscourseURL, '_blank');
        },
        clickComments: function() {
            this.manuallyClosedComments = this.commentsAreOpen;
            this.commentsAreOpen = ! this.commentsAreOpen;
        },
        showComments: function() {
            this.commentsAreOpen = false;
            this.$store.commit('setShowDialog', {dialog: 'comments', value: true});
        },
        showComment: function(comment) {
            this.commentsAreOpen = false;
            const commentURL = `${this.baseDiscourseURL}/${comment.post_number}`
            window.open(this.baseDiscourseURL, '_blank');
        },
        askQuestion: function() {
            this.commentsAreOpen = false;
            const d = this.$store.state.captionData;
            let captionIdx = this.$store.state.playingCaptionIdx;
            if (Array.isArray(captionIdx)) captionIdx = captionIdx[0];
            if (captionIdx === null) {
                window.open(this.baseDiscourseURL, '_blank');
                return;
            }
            const dict = captionArrayToDict(d.lines[captionIdx], d);
            const wordData = getWordData(dict, this.$store.state.options.displayTranslation, captionIdx);
            const hz = wordData.hz.join(' ');
            const py = wordData.py.join(' ');
            const translation = wordData.translation;
            const showId = this.$store.state.playingShowId;
            const season = this.$store.state.playingSeason;
            const episode = this.$store.state.playingEpisode;
            const timestamp = secondsToTimestamp(dict.t0);
            const header = (this.showInfo.type === 'movie'? '' : `${getSeasonName(this.showInfo, season)}${getEpisodeName(this.showInfo, season, episode)} - `) + timestamp
            const quote = `> [${header}](https://lazybug.ai/${showId}/${season+1}/${episode+1}/${captionIdx+1})\n${hz}\n${py}\n${translation}\n`;
            const URL = `${this.baseDiscourseURL}?reply_quote=${encodeURIComponent(quote)}`;
            window.open(URL, '_blank');
        },
    },
};
</script>

<style>
.q-fab__actions {
    top: -10px; /* fixes alignment on mobile */
}

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
    height: auto;
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
    top: 70px;
}

.commentselector .q-fab__actions {
    flex-wrap: wrap !important;
    justify-content: left !important;
}

.comment {
    min-width: 120px !important;
}

blockquote {
  background: #f9f9f9;
  border-left: 10px solid #ccc;
  margin: 1.5em 10px;
  padding: 0.5em 10px;
}

blockquote:before {
  color: #ccc;
  content: open-quote;
  font-size: 4em;
  line-height: 0.1em;
  margin-right: 0.25em;
  vertical-align: -0.4em;
}

blockquote p {
  display: inline;
}
</style>
