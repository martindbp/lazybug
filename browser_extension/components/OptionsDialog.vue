<template>
    <q-dialog v-model="show" dark>
        <q-card style="width: 400px" class="q-px-sm q-pb-md">
            <q-card-section>
                <div class="text-h6">Knowledge Levels</div>
            </q-card-section>
            <q-item-label header>Hanzi</q-item-label>
            <q-item dense>
                <q-item-section>
                    <q-slider color="teal" v-model="hanziKnownLevel" :min="0" :max="6" :step="1" label snap markers></q-slider>
                </q-item-section>
            </q-item>

            <q-item-label header>Pinyin</q-item-label>
            <q-item dense>
                <q-item-section>
                    <q-slider color="teal" v-model="pinyinKnownLevel" :min="0" :max="6" :step="1" label snap markers></q-slider>
                </q-item-section>
            </q-item>

            <q-item-label header>Word Translation</q-item-label>
            <q-item dense>
                <q-item-section>
                    <q-slider color="teal" v-model="translationKnownLevel" :min="0" :max="6" :step="1" label snap markers></q-slider>
                </q-item-section>
            </q-item>
            <q-card-actions align="right" class="text-teal">
                <q-btn flat label="OK" @click="clickClose"></q-btn>
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>
export default {
    components: { },
    data: function() { return {
        levels: ['None', 'HSK1', 'HSK2', 'HSK3', 'HSK4', 'HSK5', 'HSK6', 'All'],
        sliders: false,
        slideAlarm: 0,
        slideVol: 0,
        slideVibration: 0,
    }},
    computed: {
        show: {
            get: function() { return this.$store.state.showOptions; },
            set: function(val) { this.$store.commit('setShowOptions', val); },
        },
        hanziKnownLevel: {
            get: function() { return this.$store.state.options.knownLevels.hz; },
            set: function(val) { this.$store.commit('setKnownLevel', {type: 'hz', level: val}); },
        },
        pinyinKnownLevel: {
            get: function() { return this.$store.state.options.knownLevels.py; },
            set: function(val) { this.$store.commit('setKnownLevel', {type: 'py', level: val}); },
        },
        translationKnownLevel: {
            get: function() { return this.$store.state.options.knownLevels.tr; },
            set: function(val) { this.$store.commit('setKnownLevel', {type: 'tr', level: val}); },
        },
        options: function() { return this.$store.state.options; },
    },
    methods: {
        clickClose: function(event) {
            // Remove the "zimuquasardialog" class from the dialog parent, otherwise there's some flickering
            document.querySelector('.zimuquasardialog').classList.remove('zimuquasardialog');
            this.show = false;
        }
    },
}
</script>
<style>

.zimuquasardialog {
    z-index: 9999;
    position: absolute;
    left: 0;
}

</style>
