<template>
    <q-dialog v-model="show" dark>
        <q-card class="q-px-sm q-pb-md" style="min-height: 600px">
            <q-tabs
              v-model="tab"
              dense
              class="text-white shadow-2"
            >
                <q-tab name="subtitle" label="Subtitle" />
                <q-tab name="knowledge" label="Knowledge" />
                <q-tab name="content" label="Content" />
                <q-tab name="keyboard" label="Keyboard" />
            </q-tabs>

            <q-tab-panels v-model="tab">
                <q-tab-panel name="knowledge" style="width: 400px">
                    Select the HSK level you know and want to hide
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

                    <q-item-label header>Word translation</q-item-label>
                    <q-item dense>
                        <q-item-section>
                            <q-slider color="teal" v-model="translationKnownLevel" :min="0" :max="6" :step="1" label snap markers></q-slider>
                        </q-item-section>
                    </q-item>
                </q-tab-panel>
                <q-tab-panel name="subtitle" style="width: 400px">
                    <div class="text-h8">Show or hide content by default</div>
                    <q-item-label header>Hanzi</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showHz" :val="null" label="Auto" />
                        <q-radio v-model="showHz" :val="false" label="Hide" />
                        <q-radio v-model="showHz" :val="true" label="Show" />
                    </div>

                    <q-item-label header>Pinyin</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showPy" :val="null" label="Auto" />
                        <q-radio v-model="showPy" :val="false" label="Hide" />
                        <q-radio v-model="showPy" :val="true" label="Show" />
                    </div>

                    <q-item-label header>Word translation</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showTr" :val="null" label="Auto" />
                        <q-radio v-model="showTr" :val="false" label="Hide" />
                        <q-radio v-model="showTr" :val="true" label="Show" />
                    </div>

                    <q-item-label header>Full sentence translation</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showFullTr" :val="false" label="Hide" />
                        <q-radio v-model="showFullTr" :val="true" label="Show" />
                    </div>

                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;"/>

                    <div class="text-h8">Chinese characters</div>
                    <div class="q-gutter-sm">
                        <q-radio v-model="characterSet" val="sm" label="Simplified" />
                        <q-radio v-model="characterSet" val="tr" label="Traditional" />
                    </div>
                </q-tab-panel>
                <q-tab-panel name="content" style="width: 400px">
                </q-tab-panel>
                <q-tab-panel name="keyboard" style="width: 400px">
                </q-tab-panel>
            </q-tab-panels>
            <q-card-actions align="right" class="text-teal absolute-bottom">
                <q-btn flat label="Close" @click="clickClose"></q-btn>
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script>
export default {
    components: { },
    data: function() { return {
        tab: Vue.ref('knowledge'),
    }},
    computed: {
        showHz: {
            get: function() { return this.$store.state.options.show.hz; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'show', key2: 'hz', value: val}); },
        },
        showPy: {
            get: function() { return this.$store.state.options.show.py; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'show', key2: 'py', value: val}); },
        },
        showTr: {
            get: function() { return this.$store.state.options.show.tr; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'show', key2: 'tr', value: val}); },
        },
        showFullTr: {
            get: function() { return this.$store.state.options.show.fullTr; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'show', key2: 'fullTr', value: val}); },
        },
        show: {
            get: function() { return this.$store.state.showOptions; },
            set: function(val) { this.$store.commit('setShowOptions', val); },
        },
        hanziKnownLevel: {
            get: function() { return this.$store.state.options.knownLevels.hz; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'knownLevels', key2: 'hz', value: val}); },
        },
        pinyinKnownLevel: {
            get: function() { return this.$store.state.options.knownLevels.py; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'knownLevels', key2: 'py', value: val}); },
        },
        translationKnownLevel: {
            get: function() { return this.$store.state.options.knownLevels.tr; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'knownLevels', key2: 'tr', value: val}); },
        },
        characterSet: {
            get: function() { return this.$store.state.options.characterSet; },
            set: function(val) { this.$store.commit('setOption', {key: 'characterSet', value: val}); },
        },
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
