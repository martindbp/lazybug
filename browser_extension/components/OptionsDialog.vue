<template>
    <q-dialog v-model="show" dark ref="optionmodal">
        <q-card class="q-px-sm q-pb-md" style="min-height: 650px">
            <q-tabs
              v-model="tab"
              dense
              class="text-white shadow-2"
            >
                <q-tab name="subtitle" label="Subtitle" />
                <q-tab name="knowledge" label="Knowledge" />
                <q-tab name="keyboard" label="Keyboard" />
                <q-tab name="other" label="Other" />
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
                    <q-item-label header>Show pinyin</q-item-label>
                    <q-btn-toggle
                        push
                        glossy
                        v-model="showPy"
                        toggle-color="primary"
                        :options="[
                            {label: 'Auto', value: null},
                            {label: 'Hide All', value: false},
                            {label: 'Show All', value: true}
                        ]"
                    />

                    <q-item-label header>Show hanzi</q-item-label>
                    <q-btn-toggle
                        push
                        glossy
                        v-model="showHz"
                        toggle-color="primary"
                        :options="[
                            {label: 'Auto', value: null},
                            {label: 'Hide All', value: false},
                            {label: 'Show All', value: true}
                        ]"
                    />

                    <q-item-label header>Show word translation</q-item-label>
                    <q-btn-toggle
                        push
                        glossy
                        v-model="showTr"
                        toggle-color="primary"
                        :options="[
                            {label: 'Auto', value: null},
                            {label: 'Hide All', value: false},
                            {label: 'Show All', value: true}
                        ]"
                    />

                    <q-item-label header>Show full sentence translation</q-item-label>
                    <q-btn-toggle
                        push
                        glossy
                        v-model="showFullTr"
                        toggle-color="primary"
                        :options="[
                            {label: 'Hide', value: false},
                            {label: 'Show', value: true}
                        ]"
                    />

                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;" />

                    Other
                    <q-item-label header>Chinese characters</q-item-label>
                    <q-btn-toggle
                        push
                        glossy
                        v-model="characterSet"
                        toggle-color="primary"
                        :options="[
                            {label: 'Simplified', value: 'sm'},
                            {label: 'Traditional', value: 'tr'}
                        ]"
                    />
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="autoPause" label="Auto-pause subtitle" />
                    </div>
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="blurCaptions" label="Blur Captions" />
                    </div>
                </q-tab-panel>
                <q-tab-panel name="keyboard" style="width: 400px">
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="keyboardShortcutsToggle" label="Toggle Keyboard Shortcuts"></q-checkbox>
                    </div>

                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;" />

                    <div class="q-gutter-sm" v-for="shortcut in shortcuts">
                        <q-btn
                            style="margin-top: 10px; width: 80%"
                            color="primary"
                            :disable="!keyboardShortcutsToggle || choosingShortcut !== null"
                            :label="choosingShortcut === shortcut[0] ? (shortcut[1] + ': <Press Key> (ESC to clear)') : (shortcut[1] + ': ' + (shortcutValues[shortcut[0]] || 'Unset'))"
                            @click="clickShortcut(shortcut[0])"
                        >
                        </q-btn>
                        <br>
                    </div>
                    <br>
                    <q-btn color="secondary" label="Reset To Default" @click="resetShortcuts" />
                </q-tab-panel>
                <q-tab-panel name="other" style="width: 400px">
                    <q-btn color="secondary" label="Clear data" @click="clearData"/>
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
        shortcuts: [
            ["next", "Next"],
            ["prev", "Previous"],
            ["replay", "Replay"],
            ["dictionary", "Dictionary"],
            ["peek", "Peek"],
            ["peekFullTr", "Peek Full Translation"],
            ["peekPy", "Peek Pinyin Row"],
            ["peekHz", "Peek Hanzi Row"],
            ["peekTr", "Peek Word Translation Row"],
        ],
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
        blurCaptions: {
            get: function() { return this.$store.state.options.blurCaptions; },
            set: function(val) { this.$store.commit('setOption', {key: 'blurCaptions', value: val}); },
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
        resetShortcuts: function() {
            this.$store.commit('setOption', {key: 'keyboardShortcuts', value: DEFAULT_SHORTCUTS});
        },
        clearData: function() {
            clearIndexedDb();
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
