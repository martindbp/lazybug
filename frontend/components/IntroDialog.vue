<template>
    <q-dialog seamless v-model="$store.state.showDialog.intro">
        <q-card class="q-px-sm q-pb-md" height="100%">
            <q-carousel
                v-model="slide"
                transition-prev="jump-right"
                transition-next="jump-left"
                animated
                control-color="primary"
                prev-icon="arrow_left"
                next-icon="arrow_right"
                swipeable
                navigation
                padding
                arrows
                height="600px"
                class="bg-white shadow-1 rounded-borders"
            >
                <q-carousel-slide name="welcome" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h4>Welcome to Lazybug</h4>
                        <p>Lazybug is a free and open-source app for learning Chinese the lazy way, by watching TV and movies</p>
                        <q-img src="https://cdn.lazybug.ai/file/lazybug-public/images/selection.png" />
                        <p>There's a unique and growing selection available thanks to advanced OCR subtitle extraction</p>
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="subtitles1" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h4>Interactive Subtitles</h4>
                        <p>The subtitles are interactive and adapt to your skill level. Hide words you know. Peek at the minimum information you need to understand, this will allow you to learn the fastest</p>
                        <q-img src="https://cdn.lazybug.ai/file/lazybug-public/images/caption1.png" />
                        <p>Click words to hide them. Click hidden words to peek. Click again to pin them back</p>
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="hsk" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h4>Select a level</h4>
                        <p>If you already have experience with Chinese, select your HSK level (words at or below this level will be automatically hidden)</p>
                        <HSKLevelSlider />
                        <p>This can be changed later in the subtitle options</p>
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="last" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h4>Account</h4>
                        <p>Lazybug stores your data in the browser and therefore doesn't require an account, but you can create one for free to sync your data to the cloud</p>
                        <q-btn color="primary" label="Register" @click="clickRegister" />
                    </div>
                </q-carousel-slide>
            </q-carousel>
            <q-card-actions align="right">
                <q-btn flat :label="slide === 'last' ? 'OK' : 'Skip'" color="primary" @click="done" v-close-popup />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>
import HSKLevelSlider from './HSKLevelSlider.vue'

export default {
    mixins: [mixin],
    components: {
        HSKLevelSlider,
    },
    data: function() { return {
        slide: 'welcome',
    }},
    methods: {
        done: function() {
            this.$store.commit('setOption', { key: 'doneIntro', value: true });
        },
        clickRegister: function() {
            this.$store.commit('setOption', { key: 'doneIntro', value: true });
            this.$store.commit('setShowDialog', { dialog: 'intro', value: false });
            this.$store.commit('setShowDialog', { dialog: 'account', value: 'register' });
        },
    }
};
</script>

<style>
</style>
