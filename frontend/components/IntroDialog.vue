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
                keep-alive
                padding
                arrows
                height="600px"
                class="rounded-borders"
            >
                <q-carousel-slide name="welcome" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h5>Welcome to Lazybug</h5>
                        <p>Lazybug is a free and open-source app for learning Chinese the lazy way, by watching TV and movies</p>
                        <q-img loading="eager" src="https://cdn.lazybug.ai/file/lazybug-public/images/selection.png" />
                        <p>There's a unique and growing selection available thanks to advanced OCR subtitle extraction</p>
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="subtitles" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h5>Interactive Subtitles</h5>
                        <p>The subtitles are interactive and adapt to your skill level. Hide words you know. Peek at the minimum information you need to understand, this will allow you to learn the fastest</p>
                        <q-img loading="eager" src="https://cdn.lazybug.ai/file/lazybug-public/images/caption1.png" />
                        <p>Click words to hide them. Click hidden words to peek. Click again to pin them back</p>
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="hsk" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h5>Select a level</h5>
                        <p>If you already have experience with Chinese, select your HSK level (words at or below this level will be automatically hidden)</p>
                        <HSKLevelSlider />
                        <p>This can be changed later in the subtitle options</p>
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="star" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h5>Star/Export Words</h5>
                        <p>You can save words for later by clicking the star button</p>
                        <q-img loading="eager" width="200px" src="https://cdn.lazybug.ai/file/lazybug-public/images/star.png" />
                        <p>From the <i>Words</i> page you can export words for use in Spaced Repetition Systems like Anki</p>
                        <q-img loading="eager" src="https://cdn.lazybug.ai/file/lazybug-public/images/export.png" />
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="extension" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h5>Browser Extension Coming Soon</h5>
                        <p>For shows other than Youtube that can't be embedded </p>
                        <q-img loading="eager" width="300px" src="https://cdn.lazybug.ai/file/lazybug-public/images/extension.png" />
                    </div>
                </q-carousel-slide>
                <q-carousel-slide name="last" class="column no-wrap flex-center">
                    <div class="q-mt-md text-center">
                        <h5>Account</h5>
                        <p>Lazybug stores your data in the browser and therefore doesn't require an account, but you can create one for free to sync your data to the cloud</p>
                        <q-btn color="primary" label="Register" @click="clickRegister" />
                    </div>
                </q-carousel-slide>
            </q-carousel>
            <q-card-actions align="right">
                <q-btn flat :label="slide === 'last' ? 'OK' : 'Skip'" color="primary" @click="skip" />
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
        askPersist: function() {
            isStoragePersisted().then(async isPersisted => {
                if (isPersisted) {
                    console.log("Storage is successfully persisted");
                } else {
                    console.log("Storage is not persisted");
                    console.log("Trying to persist");
                    if (await persist()) {
                        console.log("We successfully turned the storage to be persisted");
                    } else {
                        console.log("Failed to make storage persisted");
                    }
                }
            });
        },
        skip: function() {
            // Terminate, or skip to last slide (which shows important account info)
            if (this.slide === 'last') {
                this.$store.commit('setShowDialog', { dialog: 'intro', value: false });
                this.$store.commit('setOption', { key: 'doneIntro', value: true });
                this.askPersist();
            }
            else {
                this.slide = 'last';
            }
        },
        clickRegister: function() {
            this.$store.commit('setOption', { key: 'doneIntro', value: true });
            this.$store.commit('setPage', 'account');
            this.$store.commit('setShowDialog', { dialog: 'intro', value: false });
            this.$store.commit('setShowDialog', { dialog: 'account', value: 'register' });
            this.askPersist();
        },
    }
};
</script>

<style>
body.body--dark .q-carousel {
    background-color: rgb(33, 33, 33) !important;
}

body.body--light .q-carousel {
    background-color: #fff;
}
</style>
