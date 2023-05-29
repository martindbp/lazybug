<template>
    <div>
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
            class="highlightedcarousel rounded-borders"
        >
            <q-carousel-slide v-for="show in highlighted" :name="show.showId" class="column no-wrap flex-center">
                <div class="q-pa-md text-center">
                    <q-img loading="eager" class="highlightedimage" :src="show.image" @click="setPlaying(show.showId)">
                        <div class="absolute-bottom text-subtitle1 text-center">
                            {{ show.description }}
                        </div>
                    </q-img>
                </div>
            </q-carousel-slide>
        </q-carousel>

        <div class="row justify-center">
            <q-btn-toggle
                glossy
                v-model="slide"
                :options="options"
            />
        </div>
    </div>
</template>

<script>

export default {
    mixins: [mixin],
    data: function() { return {
        slide: 'threebodytencent',
    }},
    computed: {
        highlighted: function() {
            if ([null, undefined].includes(this.$store.state.showList)) return [];
            const highlightedShows = [];
            for (const name of Object.keys(this.$store.state.showList)) {
                const show = this.$store.state.showList[name];
                if (show.highlighted) highlightedShows.push(show);
            }
            return highlightedShows.sort((show) => show.date_added);
        },
        options: function() {
            const options = [];
            for (let i = 0; i < this.highlighted.length; i++) {
                options.push({ label: i+1, value: this.highlighted[i].showId });
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
};
</script>

<style>

.highlightedimage {
    min-height: 50vh !important;
    max-height: 70vh !important;
    width: 50vh !important;
    cursor: pointer;
}

.highlightedcarousel .q-carousel__slide {
    min-height: auto !important;
}

.highlightedcarousel .q-tab-panel {
    padding: 0;
}
</style>
