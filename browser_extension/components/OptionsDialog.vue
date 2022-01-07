<template>
    <q-dialog v-model="show" dark>
        <q-card style="width: 300px" class="q-px-sm q-pb-md">
            <q-card-section>
                <div class="text-h6">Hanzi known level</div>
            </q-card-section>
            <q-select filled v-model="hanziKnownLevel" :options="levels" label="Filled" />


            <q-item-label header>Media volume</q-item-label>
            <q-item dense>
                <q-item-section avatar>
                    <q-icon name="volume_up"></q-icon>
                </q-item-section>
                <q-item-section>
                    <q-slider color="teal" v-model="slideVol" :step="0"></q-slider>
                </q-item-section>
            </q-item>

            <q-item-label header>Alarm volume</q-item-label>
            <q-item dense>
                <q-item-section avatar>
                    <q-icon name="alarm"></q-icon>
                </q-item-section>
                <q-item-section>
                    <q-slider color="teal" v-model="slideAlarm" :step="0"></q-slider>
                </q-item-section>
            </q-item>

            <q-item-label header>Ring volume</q-item-label>
            <q-item dense>
                <q-item-section avatar>
                    <q-icon name="vibration"></q-icon>
                </q-item-section>
                <q-item-section>
                    <q-slider color="teal" v-model="slideVibration" :step="0"></q-slider>
                </q-item-section>
            </q-item>
            <q-input filled label="Filled"></q-input>
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
            get: function() { return this.$store.state.options.hanziKnownLevel; },
            set: function(val) { this.$store.commit('setOption', {key: 'hanziKnownLevel', val: val}); },
        },
        pinyinKnownLevel: {
            get: function() { return this.$store.state.options.pinyinKnownLevel; },
            set: function(val) { this.$store.commit('setOption', {key: 'pinyinKnownLevel', val: val}); },
        },
        translationKnownLevel: {
            get: function() { return this.$store.state.options.translationKnownLevel; },
            set: function(val) { this.$store.commit('setOption', {key: 'translationKnownLevel', val: val}); },
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
