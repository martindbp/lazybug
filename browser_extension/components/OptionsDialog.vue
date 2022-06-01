<template>
    <q-dialog v-model="show" dark ref="optionmodal">
        <q-card class="q-px-sm q-pb-md" style="min-height: 500px">
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
                    Select the HSK level you want to hide automatically
                    <q-item dense>
                        <q-item-section>
                            <q-slider
                                color="teal"
                                v-model="hideWordsLevel"
                                :min="0"
                                :max="7"
                                :step="1"
                                :label-value="hideWordsLevel < 7 ? hideWordsLevel : 'all'"
                                label
                                snap
                                markers
                            />
                        </q-item-section>
                    </q-item>
                </q-tab-panel>
                <q-tab-panel name="subtitle" style="width: 400px">
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
                    <q-item-label header>Display translation (if available)</q-item-label>
                    <q-btn-toggle
                        push
                        glossy
                        v-model="displayTranslation"
                        toggle-color="primary"
                        :options="[
                            {label: 'Human', value: 0},
                            {label: 'Machine', value: 1}
                        ]"
                    />
                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;" />
                    <div class="q-gutter-sm">
                        <br>
                        <q-item-label>Auto Pause</q-item-label>
                        <q-radio v-model="autoPause" val="off" label="Off" />
                        <q-radio v-model="autoPause" val="basic" label="After every subtitle" />
                        <q-radio v-model="autoPause" val="WPS" label="After fast subtitles" />
                        <br>
                        <div v-if="autoPause === 'WPS'">
                            <q-item-label header>Words Per Second</q-item-label>
                            <q-slider label v-model="WPSThreshold" :min="0.0" :max="4.0" step="0.1" />
                        </div>
                    </div>
                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;" />
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="blurCaptions" label="Blur Captions" />
                    </div>
                    <!--
                    <div class="q-gutter-sm">
                        <q-item-label header>Timing Offset</q-item-label>
                        <q-slider
                            v-model="timingOffset"
                            label
                            label-always
                            selection-color="transparent"
                            :min="-3.0"
                            :max="3.0"
                            :step="0.05"
                        />
                    </div>
                    -->
                </q-tab-panel>
                <q-tab-panel name="keyboard" style="width: 400px">
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="keyboardShortcutsToggle" label="Toggle Keyboard Shortcuts"></q-checkbox>
                    </div>

                    <q-separator color="orange" style="margin-top: 10px; margin-bottom: 10px;" />

                    <div class="q-gutter-sm" v-for="shortcut in shortcuts">
                        <q-btn
                            style="margin-top: 10px; width: 80%"
                            size="sm"
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
                    <div class="q-gutter-sm">
                        <q-btn
                            style="margin-top: 10px; width: 80%"
                            color="primary"
                            label="Export Hanzi SRT"
                            @click="exportSrt('hanzi')"
                        />
                        <q-btn
                            style="margin-top: 10px; width: 80%"
                            color="primary"
                            label="Export English SRT"
                            @click="exportSrt('english')"
                        />
                    </div>
                    <br>
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
        autoPauseOptions: [
            { label: 'Off', value: 'off' },
            { label: 'After every subtitle', value: 'basic' },
            { label: 'After fast subtitles', value: 'WPS' },
        ],
        autoPause: 'off',
    }},
    computed: {
        show: {
            get: function() { return this.$store.state.showOptions; },
            set: function(val) { this.$store.commit('setShowOptions', val); },
        },
        timingOffset: {
            get: function() { return this.$store.state.timingOffset; },
            set: function(val) { this.$store.commit('setTimingOffset', val); },
        },
        hideWordsLevel: {
            get: function() { return this.$store.state.options.hideWordsLevel; },
            set: function(val) { this.$store.commit('setOption', {key: 'hideWordsLevel', value: val}); },
        },
        characterSet: {
            get: function() { return this.$store.state.options.characterSet; },
            set: function(val) { this.$store.commit('setOption', {key: 'characterSet', value: val}); },
        },
        displayTranslation: {
            get: function() { return this.$store.state.options.displayTranslation; },
            set: function(val) { this.$store.commit('setOption', {key: 'displayTranslation', value: val}); },
        },
        autoPause: {
            get: function() { return this.$store.state.options.autoPause; },
            set: function(val) { this.$store.commit('setOption', {key: 'autoPause', value: val}); },
        },
        WPSThreshold: {
            get: function() { return this.$store.state.options.WPSThreshold; },
            set: function(val) { this.$store.commit('setOption', {key: 'WPSThreshold', value: val}); },
        },
        blurCaptions: {
            get: function() { return this.$store.state.options.blurCaptions; },
            set: function(val) { this.$store.commit('setBlur', val); },
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
        exportSrt: function(type) {
            let srtOut = '';
            const captionData = this.$store.state.captionData;
            for (let i = 0; i < captionData.lines.length; i++) {
                const line = captionData.lines[i];
                const data = captionArrayToDict(line, captionData);
                srtOut += `${i+1}\n`;
                const t0 = srtTimestamp(data.t0);
                const t1 = srtTimestamp(data.t1);
                srtOut += `${t0} -->  ${t1}\n`;
                if (type === 'hanzi') {
                    srtOut += data.texts.join(' ');
                }
                else {
                    srtOut += data.translations[0];
                }
                srtOut += '\n\n';
            }

            let [showName, seasonName, episodeName] = getShowSeasonEpisodeName(this.$store.state.showInfo, this.$store.state.captionId);
            let name = `${showName.hz || showName}`;
            if (seasonName) name += `-${seasonName}`;
            name += `-${episodeName}`;

            let filename = `${name}-${type}.srt`;
            download(filename, srtOut);
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
