<template>
    <q-dialog v-model="show" dark ref="optionmodal">
        <q-card class="q-px-sm q-pb-md" style="min-height: 600px">
            <q-tabs
              v-model="tab"
              dense
              class="text-white shadow-2"
            >
                <q-tab name="subtitle" label="Subtitle" />
                <q-tab name="knowledge" label="Knowledge" />
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
                    <q-item-label header>Show hanzi</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showHz" :val="null" label="Auto" />
                        <q-radio v-model="showHz" :val="false" label="Hide" />
                        <q-radio v-model="showHz" :val="true" label="Show" />
                    </div>

                    <q-item-label header>Show pinyin</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showPy" :val="null" label="Auto" />
                        <q-radio v-model="showPy" :val="false" label="Hide" />
                        <q-radio v-model="showPy" :val="true" label="Show" />
                    </div>

                    <q-item-label header>Show word translation</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showTr" :val="null" label="Auto" />
                        <q-radio v-model="showTr" :val="false" label="Hide" />
                        <q-radio v-model="showTr" :val="true" label="Show" />
                    </div>

                    <q-item-label header>Show full sentence translation</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="showFullTr" :val="false" label="Hide" />
                        <q-radio v-model="showFullTr" :val="true" label="Show" />
                    </div>

                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;" />

                    Other
                    <q-item-label header>Chinese characters</q-item-label>
                    <div class="q-gutter-sm">
                        <q-radio v-model="characterSet" val="sm" label="Simplified" />
                        <q-radio v-model="characterSet" val="tr" label="Traditional" />
                    </div>
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="autoPause" label="Auto-pause subtitle" />
                    </div>
                </q-tab-panel>
                <q-tab-panel name="keyboard" style="width: 400px">
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="keyboardShortcutsToggle" label="Toggle Keyboard Shortcuts"></q-checkbox>
                    </div>

                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;" />

                    <div class="q-gutter-sm" v-for="shortcut in shortcuts">
                        <q-btn
                            style="margin-top: 10px"
                            color="primary"
                            :disable="!keyboardShortcutsToggle || choosingShortcut !== null"
                            :label="choosingShortcut === shortcut[0] ? (shortcut[1] + ': <Press Key> (ESC to clear)') : (shortcut[1] + ': ' + (shortcutValues[shortcut[0]] || 'Unset'))"
                            @click="clickShortcut(shortcut[0])"
                        >
                        </q-btn>
                        <br>
                    </div>
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
        shortcuts: [["peek", "Peek"], ["next", "Next"], ["prev", "Previous"], ["replay", "Replay"], ["dictionary", "Dictionary"]],
        choosingShortcut: null,
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
        autoPause: {
            get: function() { return this.$store.state.options.autoPause; },
            set: function(val) { this.$store.commit('setOption', {key: 'autoPause', value: val}); },
        },
        keyboardShortcutsToggle: {
            get: function() { return this.$store.state.options.keyboardShortcutsToggle; },
            set: function(val) { this.$store.commit('setOption', {key: 'keyboardShortcutsToggle', value: val}); },
        },
        shortcutValues: function() {
            return this.$store.state.options.keyboardShortcuts;
        },
    },
    methods: {
        clickClose: function(event) {
            // Remove the "zimuquasardialog" class from the dialog parent, otherwise there's some flickering
            document.querySelector('.zimuquasardialog').classList.remove('zimuquasardialog');
            this.show = false;
        },
        clickShortcut: function(shortcut) {
            this.choosingShortcut = shortcut;
            const self = this;
            window.addEventListener("keydown", function(event) {
                event.preventDefault();
                event.stopPropagation();
                const val = event.code === 'Escape' ? null : event.code;
                self.$store.commit('setDeepOption', {key: 'keyboardShortcuts', key2: shortcut, value: val});
                self.choosingShortcut = null;
            }, {once: true, capture: true});
        },
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
