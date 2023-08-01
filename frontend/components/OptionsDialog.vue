<template>
    <q-dialog seamless v-model="show" dark ref="optionmodal" class="fixoptionsdialogheight">
        <q-card dark class="q-px-sm q-pb-md" style="min-height: 500px">
            <q-tabs
              v-model="tab"
              dense
              dark
              class="text-white shadow-2"
            >
                <q-tab dark name="subtitle" label="Subtitles" />
                <q-tab dark name="learning" label="Learning" />
                <q-tab dark name="keyboard" label="Keyboard" />
                <q-tab dark name="other" label="Other" />
            </q-tabs>

            <q-tab-panels dark v-model="tab">
                <q-tab-panel class="no-scroll" name="subtitle" style="width: 400px">
                    <q-btn-toggle
                        size="sm"
                        push
                        glossy
                        v-model="characterSet"
                        toggle-color="primary"
                        :options="[
                            {label: 'Simplified Characters', value: 'sm'},
                            {label: 'Traditional Characters', value: 'tr'}
                        ]"
                    />
                    <q-item-label header>Prefer</q-item-label>
                    <q-btn-toggle
                        size="sm"
                        push
                        glossy
                        v-model="displayTranslation"
                        toggle-color="primary"
                        :options="[
                            {label: 'Human translations', value: 0},
                            {label: 'Machine translations', value: 1}
                        ]"
                    />
                    <q-item-label header>Smart Subtitles</q-item-label>
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="useSmartSubtitles" label="Use Smart Subtitles" />
                    </div>
                    <div v-if="useSmartSubtitles">
                        <q-item-label header>Your HSK level</q-item-label>
                        <q-item dense>
                            <q-item-section>
                                <HSKLevelSlider />
                            </q-item-section>
                        </q-item>

                        <q-item-label header>Add word list</q-item-label>
                        <q-item dense>
                            <q-btn color="primary" label="Upload Word List" @click="uploadWordList" size="sm" />
                            <q-btn style="margin-left: 5px" v-if="$store.state.options.personalKnownVocabulary.length > 0" color="red" label="Clear Words" @click="clearWordList" size="sm" />
                        </q-item>

                        <q-item-label header>Show</q-item-label>
                        <q-checkbox v-model="showPy" label="Show pinyin row" />
                        <!--<q-checkbox v-model="showHz" label="Show hanzi row" />-->
                        <q-checkbox v-model="showTr" label="Show translation row" />
                        <q-checkbox v-model="showTranslation" label="Show full translation" />
                    </div>
                    <q-item-label header>Other</q-item-label>
                    <div class="q-gutter-sm">
                        <q-checkbox v-model="blurCaptions" label="Blur Captions" />
                    </div>
                    <!--
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
                    -->
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
                <q-tab-panel class="no-scroll" name="learning" style="width: 400px">
                    <q-item-label header>Star Word Exercises</q-item-label>
                    <q-btn-toggle
                        push
                        glossy
                        v-model="exercisesOn"
                        toggle-color="primary"
                        :options="[
                            {label: 'On', value: true},
                            {label: 'Off', value: false}
                        ]"
                    />
                    <q-item-label header>How many correct answers counts as known?</q-item-label>
                    <q-item dense>
                        <q-item-section>
                            <q-slider
                                color="teal"
                                v-model="exercisesKnownThreshold"
                                :min="1"
                                :max="15"
                                :step="1"
                                :label-value="exercisesKnownThreshold"
                                label
                                snap
                                markers
                            />
                        </q-item-section>
                    </q-item>
                    <q-item dense>
                        <q-btn color="primary" label="Clear Personal Translations" @click="clearPersonalExerciseTranslations" />
                    </q-item>
                </q-tab-panel>
                <q-tab-panel class="no-scroll" name="keyboard" style="width: 400px">
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
                <q-tab-panel class="no-scroll" name="other" style="width: 400px">
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
import HSKLevelSlider from './HSKLevelSlider.vue'

export default {
    props: ['playerId'],
    mixins: [mixin],
    components: {
        HSKLevelSlider,
    },
    data: function() { return {
        tab: Vue.ref('subtitle'),
        shortcuts: [
            ["next", "Next"],
            ["prev", "Previous"],
            ["replay", "Replay"],
            ["dictionary", "Dictionary"],
            ["pausePlay", "Pause/Play"],
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
        keyboardListener: null,
    }},
    mounted: function() {
        const self = this;
        this.keyboardListener = window.addEventListener("keydown", function(event) {
            if(event.key === "Escape") self.show = false;
        }, {capture: false});
    },
    beforeDestroy: function() {
        window.removeEventListener('keydown', this.keyboardListener);
    },
    computed: {
        show: {
            get: function() { return this.$store.state.showDialog.options; },
            set: function(val) { this.$store.commit('setShowDialog', {dialog: 'options', value: val}); },
        },
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
        showTranslation: {
            get: function() { return this.$store.state.options.show.translation; },
            set: function(val) { this.$store.commit('setDeepOption', {key: 'show', key2: 'translation', value: val}); },
        },
        timingOffset: {
            get: function() { return this.$store.state.timingOffset; },
            set: function(val) { this.$store.commit('setTimingOffset', val); },
        },
        exercisesOn: {
            get: function() { return this.$store.state.options.exercisesOn; },
            set: function(val) { this.$store.commit('setOption', {key: 'exercisesOn', value: val}); },
        },
        exercisesKnownThreshold: {
            get: function() { return this.$store.state.options.exercisesKnownThreshold; },
            set: function(val) { this.$store.commit('setOption', {key: 'exercisesKnownThreshold', value: val}); },
        },
        useSmartSubtitles: {
            get: function() { return this.$store.state.options.useSmartSubtitles; },
            set: function(val) { this.$store.commit('setOption', {key: 'useSmartSubtitles', value: val}); },
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
        clearWordList: function() {
            const count = this.$store.state.options.personalKnownVocabulary.length;
            this.$store.commit('setOption', {key: 'personalKnownVocabulary', value: []});
            this.$q.dialog({
                title: 'Done',
                message: `Cleared ${count} words`,
            });
        },
        uploadWordList: function() {
            var fileChooser = document.createElement("input");
            fileChooser.style.display = 'none';
            fileChooser.type = 'file';

            const self = this;
            fileChooser.addEventListener('change', function (evt) {
                var f = evt.target.files[0];
                if(f) {
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        const lines = e.target.result.split('\n');
                        const hanzis = [];
                        for (const line of lines) {
                            const hanzi = filterTextHanzi(line);
                            if (hanzi.length > 0) hanzis.push(hanzi);
                        }


                        const currWords = new Set(self.$store.state.options.personalKnownVocabulary);
                        const newWords = new Set(hanzis);

                        const union = new Set([...currWords, ...hanzis]);
                        const numAdded = union.size - currWords.size;
                        const duplicates = newWords.size - numAdded;

                        self.$store.commit('setOption', {key: 'personalKnownVocabulary', value: [...union]});
                        self.$q.dialog({
                            title: 'Success',
                            message: `Added ${numAdded} words, ${duplicates} duplicates`,
                        });
                    }
                    reader.readAsText(f);
                }
            });

            document.body.appendChild(fileChooser);
            fileChooser.click();
        },
        clearPersonalExerciseTranslations: function() {
            this.$store.commit('setOption', {key: 'personalExerciseTranslations', value: {}});
        },
        clickClose: function(event) {
            // Remove the "lazybugquasardialog" class from the dialog parent, otherwise there's some flickering
            let dialog = document.querySelector('.lazybugquasardialog');
            if (dialog) {
                dialog.classList.remove('lazybugquasardialog');
            }
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
            const captionData = this.captionData;
            for (let i = 0; i < captionData.lines.length; i++) {
                const data = captionArrayToDict(captionData.lines, i, captionData);
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

            let [showName, seasonIdx, seasonName, episodeIdx, episodeName] = getShowSeasonEpisode(getShowInfo(this.playerId, this.$store), this.captionId);
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

.lazybugquasardialog {
    z-index: 9999;
    position: absolute;
    left: 0;
}

.q-card.highlight {
    border: 2px solid red;
}

.fixoptionsdialogheight .q-panel {
    height: auto !important;
}

.fixoptionsdialogheight .q-panel > div {
    height: auto !important;
}

</style>
