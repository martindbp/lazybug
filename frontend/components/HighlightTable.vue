<template>
    <div :class="{'row': true, 'justify-center': true, 'mobile': isMobile}">
        <q-carousel
            v-model="slide"
            prev-icon="arrow_left"
            next-icon="arrow_right"
            transition-prev="slide-right"
            transition-next="slide-left"
            swipeable
            animated
            keep-alive
            control-color="primary"
            navigation
            arrows
            class="highlightedcarousel rounded-borders"
            style="display: inline-block"
        >
            <q-carousel-slide v-for="group in highlightGroups" :name="group[0].showId" class="column no-wrap flex-center row justify-center">
                <div class="row fit justify-start items-center q-gutter-xs q-col-gutter no-wrap">
                    <div v-for="show in group" class="q-pa-md text-center">
                        <q-img loading="eager" class="highlightedimage" :src="show.image" @click="setPlaying(show.showId)">
                            <div class="absolute-bottom text-subtitle1 text-center">
                                {{getShowName(show)}}: {{ show.description }}
                            </div>
                        </q-img>
                    </div>
                </div>
            </q-carousel-slide>
        </q-carousel>
    </div>
</template>

<script>

export default {
    mixins: [mixin],
    data: function() { return {
        slide: null,
    }},
    computed: {
        groupN: function() {
            return this.isMobile ? 1 : 2;
        },
        highlighted: function() {
            if ([null, undefined].includes(this.$store.state.showList)) return [];
            const highlightedShows = [];
            for (const name of Object.keys(this.$store.state.showList)) {
                const show = this.$store.state.showList[name];
                if (show.highlighted) highlightedShows.push(show);
            }
            return highlightedShows.sort((show) => show.date_added);
        },
        highlightGroups: function() {
            const groups = [];

            let nextGroup = [];
            for (const show of this.highlighted) {
                nextGroup.push(show);
                if (nextGroup.length === this.groupN) {
                    groups.push(nextGroup);
                    nextGroup = [];
                }
            }
            if (nextGroup.length > 0) groups.push(nextGroup);
            return groups;
        },
        options: function() {
            const options = [];
            for (let i = 0; i < this.highlightGroups.length; i++) {
                options.push({ label: i+1, value: this.highlightGroups[i][0].showId });
            }
            return options;
        },
    },
    watch: {
        options: {
            immediate: true,
            handler: function(newValue, oldValue) {
                this.slide = newValue[0].value;
            },
        }
    },
    methods: {
        getShowName: function(show) {
            return resolveShowName(show.name);
        },
    },
};
</script>

<style>

.highlightedimage {
    cursor: pointer;
}

.highlightedimage {
    height: 70vh !important;
    width: 25vw !important;
}

.mobile .highlightedimage {
    height: 60vh !important;
    width: 70vw !important;
}

.highlightedcarousel .q-carousel__slide {
    min-height: auto !important;
}

.highlightedcarousel .q-tab-panel {
    padding: 0;
}

.highlightedcarousel .q-carousel__navigation--bottom {
    bottom: -10px;
}

.highlightedcarousel .q-carousel__next-arrow {
    right: 0;
}

.highlightedcarousel .q-carousel__prev-arrow {
    left: 0;
}
</style>
