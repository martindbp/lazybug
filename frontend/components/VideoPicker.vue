<template>
    <div v-if="showInfo && showInfo.type !== 'movie'" :class="{videopicker: true, mobile: isMobile}">
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
</template>

<script>

export default {
    mixins: [mixin],
    props: {
        hidden: { default: false },
    },
    data: function() { return {
        clickEventListener: null,
    }},
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
