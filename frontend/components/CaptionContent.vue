<template>
    <div ref="captioncontent" :class="{captioncontent: true}">
        <table :class="{contenttable: true, plain: !smart, extrapaddingtop: !$store.state.options.show.py, extrapaddingbottom: !$store.state.options.show.tr && !$store.state.options.show.translation}" ref="wordcontent">
            <tr class="toprow" v-if="smart && $store.state.options.show.py">
                <td v-if="data !== null" title="Peek pinyin row" :class="getClasses('py', null, true)" @click="clickPeekRow('py')" >
                    <span v-if="! $store.state.options.pin.py" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="$store.state.options.pin.py" class="iconcard peek cardcontent" v-html="pinIcon" style="visibility: visible !important"></span>
                    <span v-else class="cardcontent">PY</span>

                    <ContentContextMenu
                        type="py"
                        :pin="showPinRow('py')"
                        :unpin="!showPinRow('py')"
                        :copy="true"
                        :options="false"
                        :click="clickRowContextMenu"
                    />
                </td>
                <td
                    :class="getClasses('py', i)"
                    v-for="(py, i) in wordData.py"
                    :key="i"
                    :style="tdStyle"
                    :ref="'pyExercise'+i"
                >
                    <div
                        v-if="pyInputSubmitted[i] !== null"
                    >
                        <span v-if="pyInputs[i].distance <= 2" v-for="charclass in pyInputs[i].chars" :class="charclass[1]">{{ charclass[0] }}</span>
                        <div style="display: inline" v-else>
                            <span class="delete">{{ pyInputs[i].input }}</span>
                            <span class="insert">{{ py }}</span>
                        </div>
                        <q-btn
                            :color="getAnswerColor(pyInputSubmitted[i])"
                            :icon="pyInputSubmitted[i] >= 0 ? 'done' : 'close'"
                            @click="flipAnswer(pyInputSubmitted, 'py', i)"
                            round
                        />
                        <q-tooltip v-if="showTooltipIdx === i" anchor="center right" self="center left" v-model="showPinyinGradingTooltip">
                            <div v-if="!lastAnswerCorrect">You can override the grading by clicking the mark</div>
                            <div>This exercise disappears after {{$store.state.options.exercisesKnownThreshold}} correct answers</div>
                        </q-tooltip>
                    </div>
                    <span
                        v-else-if="showExercise('py', i)"
                        class="cardcontent"
                    >
                        <q-input
                            :autofocus="i == 0"
                            spellcheck="false"
                            @keyup.enter="onPyInputEnter(i)"
                            @keydown.tab.stop.prevent="onInputTab('py', i)"
                            :ref="'pyInput_'+i"
                            class="starinput"
                            borderless
                            dark
                            v-model="pyInputs[i]"
                            label=""
                        />
                        <q-tooltip v-if="showTooltipIdx === i" anchor="center right" self="center left" v-model="showPinyinTooltip">
                            <div>You starred a word, can you remeber the pinyin?</div>
                            <div>Type 1-5 after a syllable to get tonal marks</div>
                        </q-tooltip>
                    </span>
                    <span
                        v-else
                        class="cardcontent"
                        :style="{opacity: hiddenAndNotPeeking.py[i] ? 0 : 1}"
                    >
                        {{ hiddenAndNotPeeking.py[i] && ! hiddenAfterTemporaryPeek.py[i] ? '-' : py }}
                    </span>
                </td>
            </tr>
            <tr class="centerrow" v-if="$store.state.options.show.hz">
                <td v-if="data !== null" title="Peek hanzi row" :class="getClasses('hz', null, true)" @click="clickPeekRow('hz')">
                    <span v-if="! $store.state.options.pin.hz" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="$store.state.options.pin.hz" class="iconcard peek cardcontent" v-html="pinIcon" style="visibility: visible !important"></span>
                    <span v-else class="cardcontent">HZ</span>

                    <ContentContextMenu
                        type="hz"
                        :pin="showPinRow('hz')"
                        :unpin="!showPinRow('hz')"
                        :copy="true"
                        :options="false"
                        :click="clickRowContextMenu"
                    />
                </td>
                <td
                    v-if="smart"
                    :class="getClasses('hz', i)"
                    @click.stop.prevent="click('hz', i)"
                    @mousemove="mouseMove"
                    v-for="(hz, i) in wordData.hz"
                    :key="i"
                    :style="tdStyle"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: hiddenAndNotPeeking.hz[i] && !$store.state.peekStates.rows.hz ? 0 : 1}"
                        :ref="'hzSpan'+i"
                    >
                        {{ sm2tr(hz) }}
                    </span>
                    <span v-if="hiddenAndNotPeeking.hz[i] || (hiddenStates.hz[i] && !$store.state.peekStates.hz[i] && $store.state.peekStates.rows.hz)" class="iconcard peek" v-html="eyecon"></span>
                    <span v-else-if="purePeekStates.hz[i] && !mouseHasNotMovedAfterPeeking[i]" class="iconcard peek" v-html="pinIcon"></span>
                    <span v-else-if="!hiddenStates.hz[i]" class="iconcard peek" v-html="hideIcon"></span>
                    <ContentContextMenu
                        type="word"
                        :idx="i"
                        :star="!hiddenAndNotPeeking.hz[i] && ! starredStates.words[i]"
                        :unstar="starredStates.words[i]"
                        :dict="true"
                        :click="clickContextMenu"
                        :copy="true"
                        :stats="wordStats[i]"
                    />
                </td>
                <td
                    v-else
                    :class="{
                        captioncard: true,
                        peeking: purePeekStates.rows.hz,
                        placeholder: !purePeekStates.rows.hz,
                        plainhz: true,
                        showborder: data !== null,
                    }"
                    :style="tdStyle"
                    @click.stop.prevent="clickPeekRow('hz')"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: !$store.state.peekStates.rows.hz ? 0 : 1}"
                    >
                        {{ wordData.text }}
                    </span>
                    <span v-if="!purePeekStates.rows.hz" class="iconcard peek" v-html="eyecon" />
                </td>
            </tr>
            <tr class="bottomrow" v-if="smart && $store.state.options.show.tr">
                <td v-if="data !== null" title="Peek word translations" :class="getClasses('tr', null, true)" @click="clickPeekRow('tr')" :style="tdStyle">
                    <span v-if="! $store.state.options.pin.tr" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="$store.state.options.pin.tr" class="iconcard peek cardcontent" v-html="pinIcon" style="visibility: visible !important"></span>
                    <span v-else class="cardcontent">TR</span>
                    <ContentContextMenu
                        type="tr"
                        :pin="showPinRow('tr')"
                        :unpin="!showPinRow('tr')"
                        :options="false"
                        :click="clickRowContextMenu"
                    />
                </td>
                <td
                    :class="getClasses('tr', i)"
                    v-for="(tr, i) in wordData.tr"
                    :key="i"
                    :style="tdStyle"
                    :ref="'trExercise'+i"
                >
                    <div
                        v-if="trInputSubmitted[i] !== null"
                    >
                        <span v-if="trInputs[i].distance <= 2" v-for="charclass in trInputs[i].chars" :class="charclass[1]">{{ charclass[0] }}</span>
                        <div style="display: inline" v-else>
                            <span class="delete">{{ trInputs[i].input }}</span>
                            <span class="insert">{{ tr }}</span>
                        </div>
                        <q-btn
                            :color="getAnswerColor(trInputSubmitted[i])"
                            :icon="trInputSubmitted[i] >= 0 ? 'done' : 'close'"
                            @click="flipAnswer(trInputSubmitted, 'tr', i)"
                            round
                        />
                        <q-tooltip v-if="showTooltipIdx === i" anchor="center right" self="center left" v-model="showTranslationGradingTooltip">
                            <div v-if="!lastAnswerCorrect">You can override the grading by clicking the mark</div>
                            <div>This exercise disappears after {{$store.state.options.exercisesKnownThreshold}} correct answers</div>
                        </q-tooltip>
                    </div>
                    <span
                        v-else-if="showExercise('tr', i)"
                        class="cardcontent"
                    >
                        <q-input
                            :tabindex="i*2 + 1"
                            spellcheck="false"
                            @keyup.enter="onTrInputEnter(i)"
                            @keydown.tab.stop.prevent="onInputTab('tr', i)"
                            :ref="'trInput_'+i"
                            class="starinput"
                            borderless
                            dark
                            v-model="trInputs[i]"
                            label=""
                        />
                    </span>
                    <span
                        v-else
                        class="cardcontent"
                        :title="!hiddenAndNotPeeking.tr[i] && tr !== null && tr.length > truncateTrLengths[i] ? tr : null"
                        :style="{opacity: hiddenAndNotPeeking.tr[i] ? 0 : 1}"
                    >
                        {{ (tr !== null && !hiddenAndNotPeeking.tr[i]) || hiddenAfterTemporaryPeek.tr[i] ? (tr.substring(0, truncateTrLengths[i]) + (tr.length > truncateTrLengths[i] ? '...' : '')) : '-' }}
                    </span>
                </td>
            </tr>
        </table>
        <table class="contenttable fulltranslationtable" :style="{ fontSize: $store.state.captionFontSize+'px !important'}" v-if="data !== null && smart && $store.state.options.show.translation">
            <tr>
                <td v-if="data !== null" title="Peek sentence translation" :class="getClasses('translation', null, true)" @click="clickPeekRow('translation')" :style="tdStyle">
                    
                    <span v-if="! $store.state.options.pin.translation" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="$store.state.options.pin.translation" class="iconcard peek cardcontent" v-html="pinIcon" style="visibility: visible !important"></span>
                    <span v-else class="cardcontent">EN</span>
                    <ContentContextMenu
                        type="translation"
                        :pin="showPinRow('translation')"
                        :unpin="!showPinRow('translation')"
                        :options="false"
                        :click="clickRowContextMenu"
                    />
                </td>
                <td
                    ref="fulltranslation"
                    @click.stop.prevent="click('translation')"
                    :class="{
                        captioncard: true,
                        peeking: purePeekStates.translation,
                        starred: starredStates.translation,
                        fulltranslation: true,
                        placeholder: hiddenAndNotPeeking.translation,
                        showborder: data !== null,
                    }"
                    :style="tdStyle"
                >
                    <span class="cardcontent" :style="{ opacity: hiddenAndNotPeeking['translation'] ? 0 : 1 }">
                        {{ translation }}
                        <q-badge v-if="starredStates.translation" class="starbadge" color="transparent" rounded floating v-html="smallStarIcon"></q-badge>
                    </span>
                    <span class="iconcard peek" v-if="hiddenAndNotPeeking.translation" v-html="eyecon"></span>
                    <ContentContextMenu
                        type="translation"
                        :star="! starredStates.translation"
                        :unstar="starredStates.translation"
                        :click="clickContextMenu"
                        :copy="true"
                        :switchT="data.translations.length > 1"
                        :switchlabel="translationIdx === 0 ? 'Switch to Machine translations' : 'Switch to Human translations'"
                    />
                </td>
            </tr>
        </table>
    </div>
</template>
<script>
import ContentContextMenu from './ContentContextMenu.vue'

export default {
    mixins: [mixin],
    components: {
        ContentContextMenu,
    },
    props: {
        playerId: { default: null },
        data: { default: null },
        trCorrectDistanceThreshold: { default: 1.0 },
    },
    data: function () { return {
        eyecon: getIconSvg("eye", 18),
        pinIcon: getIconSvg("pin", 18),
        hideIcon: getIconSvg("hide", 18),
        unpinIcon: getIconSvg("unpin", 18),
        smallStarIcon: getIconSvg("star", 10, 'darkorange'),
        timeouts: [],
        mouseHasNotMovedAfterPeeking: false,
        pyInputs: Vue.ref([]),
        trInputs: Vue.ref([]),
        pyInputSubmitted: Vue.ref([]),  // null if not submitted, delta (-1, 0, 1) if submitted
        trInputSubmitted: Vue.ref([]),
        hasExercises: false,
        lastPausedExerciseIdxTime: null,
        showTooltipIdx: -1,
        showPinyinTooltip: false,
        showPinyinGradingTooltip: false,
        showTranslationGradingTooltip: false,
        showFinalHelpTooltip: false,
        lastAnswerCorrect: false,
    }},
    computed: {
        allExercisesAnswered: function() {
            for (let i = 0; i < this.pyInputSubmitted.length; i++) {
                const sub = this.pyInputSubmitted[i];
                if (sub === null && this.showExercise('py', i)) return false;
            }
            for (let i = 0; i < this.trInputSubmitted.length; i++) {
                const sub = this.trInputSubmitted[i];
                if (sub === null && this.showExercise('tr', i)) return false;
            }
            return true;
        },
        exercisesOn: function() {
            return this.$store.state.options.exercisesOn || this.isReviewSession;
        },
        currentCaptionIdx: function() {
            return this.data.idx;
        },
        smart: function() {
            return this.$store.state.options.useSmartSubtitles;
        },
        tdStyle: function() {
            return {
                fontSize: this.$store.state.captionFontSize+'px !important',
            };
        },
        wordStats: function() {
            const stats = [];
            for (var i = 0; i < this.wordData.hz.length; i++) {
                const key = `${this.wordData.hz[i]}-${this.wordData.py[i]}`;
                stats.push(this.videoWordStats[key]);
            }
            return stats;
        },
        truncateTrLengths: function() {
            let outLengths = [];
            for (let i = 0; i < this.data.alignments.length; i++) {
                const trunateLength = truncateTranslationLength(this.wordData.py[i], this.wordData.hz[i]);
                outLengths.push(trunateLength);
            }
            return outLengths;
        },
        translationIdx: function() {
            if (this.data == null) return null;
            return Math.min(this.$store.state.options.displayTranslation, this.data.translations.length-1);
        },
        translation: function() {
            if (this.translationIdx == null) return '';
            return this.data.translations[this.translationIdx];
        },
        texts: function() {
            const sm = this.data.texts.join(' ');
            return {
                sm: sm,
                tr: this.sm2tr(sm),
            };
        },
        wordData: function() {
            return getWordData(this.data, this.translationIdx, this.currentCaptionIdx);
        },
        hiddenAndNotPeeking: function() {
            const states = {'py': [], 'hz': [], 'tr': [], 'translation': this.hiddenStates['translation'] && ! this.purePeekStates['translation']};
            for (let i = 0; i < this.wordData.hz.length; i++) {
                for (var type of STATE_ORDER) {
                    states[type][i] = this.hiddenStates[type][i] && ! this.purePeekStates[type][i];
                }
            }
            return states;
        },
        hiddenAfterTemporaryPeek: function() {
            const states = {'py': [], 'hz': [], 'tr': []};
            for (let i = 0; i < this.wordData.hz.length; i++) {
                for (var type of STATE_ORDER) {
                    states[type][i] = this.$store.state.peekStates[type][i] === 'hiddenAfterTemporaryPeek';
                }
            }
            return states;
        },
        hiddenStates: function() {
            return hiddenStates(this.$store.state.states, this.wordData);
        },
        starredStates: function() {
            return starredStates(this.$store.state.states, this.wordData);
        },
        numCorrect: function() {
            return getNumCorrect(this.$store.state.states, this.wordData);
        },
    },
    updated: function() {
        if (! this.smart) return;

        // New text may have changed the size of the caption, so need to update width of full translation table
        // Also, set width of any exercise inputs
        const self = this;
        this.$nextTick(function () {
            self.updateWidths();
        });
    },
    watch: {
        pyInputs: {
            deep: true,
            handler: function() {
                // Convert pys to diacritical
                for (let i = 0; i < this.pyInputs.length; i++) {
                    if (this.pyInputSubmitted[i] !== null) continue;
                    const diacritical = normalizedToDiacritical(this.pyInputs[i]);
                    if (diacritical !== this.pyInputs[i]) {
                        this.pyInputs[i] = diacritical;
                    }
                }
            },
        },
        data: {
            immediate: true,
            handler: function(newData, oldData) {
                if (newData !== oldData) {
                    for (const timeout of this.timeouts) {
                        clearTimeout(timeout);
                    }
                    this.timeouts = [];

                    this.showTooltipIdx = -1;
                    this.showPinyinTooltip = false;
                    this.showPinyinGradingTooltip = false;
                    this.showTranslationGradingTooltip = false;
                    this.showFinalHelpTooltip = false;

                    this.$store.commit('resetPeekStates', this.wordData.hz.length);
                    if (this.$store.state.options.useSmartSubtitles) {
                        this.applyLvlStates();
                        this.applyPersonalKnownVocab();
                        this.applyComponents();
                        this.applyCompoundWordsNotInDict();
                        this.applySimpleCompounds();
                    }
                    this.applyPinnedRows();

                    this.lastPausedExerciseIdxTime = null;
                    this.pyInputs.length = 0;
                    this.pyInputSubmitted.length = 0;
                    this.trInputs.length = 0;
                    this.trInputSubmitted.length = 0;
                    this.mouseHasNotMovedAfterPeeking = [];
                    for (let i = 0; i < this.wordData.hz.length; i++) {
                        this.mouseHasNotMovedAfterPeeking.push(false);
                        this.pyInputs.push('');
                        this.pyInputSubmitted.push(null);
                        this.trInputs.push('');
                        this.trInputSubmitted.push(null);
                    }

                    if (this.submittedExercises[newData.idx]) {
                        this.pyInputSubmitted = deepCopy(this.submittedExercises[newData.idx].pyInputSubmitted);
                        this.trInputSubmitted = deepCopy(this.submittedExercises[newData.idx].trInputSubmitted);
                        this.pyInputs = deepCopy(this.submittedExercises[newData.idx].pyInputs);
                        this.trInputs = deepCopy(this.submittedExercises[newData.idx].trInputs);
                    }

                    this.hasExercises = false;
                    for (let i = 0; i < this.hiddenAndNotPeeking.py.length; i++) {
                        if (
                            this.showExercise('py', i) ||
                            this.showExercise('tr', i) ||
                            this.pyInputSubmitted[i] !== null ||
                            this.trInputSubmitted[i] !== null
                        ) {
                            this.$store.commit('setPeekState', {'type': 'hz', 'i': i, value: true});
                        }

                        if (this.showExercise('py', i) && !this.showExercise('tr', i)) {
                            this.$store.commit('setPeekState', {'type': 'tr', 'i': i, value: true});
                        }
                        else if (this.showExercise('tr', i) && !this.showExercise('py', i)) {
                            this.$store.commit('setPeekState', {'type': 'py', 'i': i, value: true});
                        }

                        if (
                            (this.showExercise('py', i) && this.pyInputSubmitted[i] === null) ||
                            (this.showExercise('tr', i) && this.trInputSubmitted[i] === null)
                        ) {
                            this.hasExercises = true;
                        }
                    }
                }

            },
        },
    },
    mounted: function() {
        const self = this;
        self.updateWidths();

        let lastTime = 0;
        setInterval(() => {
            const currentTime = self.videoAPI.getCurrentTime();
            if (currentTime < lastTime) {
                self.lastPausedExerciseIdxTime = null;
            }
            lastTime = currentTime;

            if (
                self.data !== null &&
                self.exercisesOn &&
                self.hasExercises &&
                ! self.allExercisesAnswered &&
                self.data.t1 - currentTime < 0.10 &&
                self.data.t1 - currentTime > -0.10 &&
                (
                    !self.lastPausedExerciseIdxTime ||
                    self.lastPausedExerciseIdxTime.idx !== self.currentCaptionIdx /*||
                    currentTime < self.lastPausedExerciseIdxTime.time*/
                )
            ) {
                self.videoAPI.pause();
                let inputInFocus = false;
                if (! (document.activeElement && document.activeElement.tagName === 'INPUT')) {
                    self.onInputTab();  // focus the first input
                }
                self.lastPausedExerciseIdxTime = {idx: self.currentCaptionIdx, time: currentTime};
            }

        }, 5);
    },
    methods: {
        getAnswerColor: function(answer) {
            if (answer === 1) return 'green';
            else if (answer === -1) return 'red';
            else if (answer === 0) return 'orange';
        },
        updateWidths: function() {
            for (let i = 0; i < this.wordData.py.length; i++) {
                const pyRef = this.$refs['pyExercise'+i];
                const trRef = this.$refs['trExercise'+i];
                const hzSpanRef = this.$refs['hzSpan'+i];
                const hzSpanWidth = hzSpanRef.clientWidth;
                if (pyRef) pyRef.style.width = hzSpanWidth + 'px';
                if (trRef) trRef.style.width = hzSpanWidth + 'px';
            }

            if ([null, undefined].includes(this.$refs.captioncontent) || [null, undefined].includes(this.$refs.fulltranslation)) {
                return;
            }
            const peekCells = this.$refs.wordcontent.children[0].children;
            if (peekCells.length > 0) {
                const topLeftWidth = peekCells[0].clientWidth;
                const totalRowWidth = this.$refs.wordcontent.clientWidth;
                this.$refs.fulltranslation.style.minWidth = (totalRowWidth - topLeftWidth) + 'px';
            }
        },
        showExercise: function(type, i) {
            return (
                this.exercisesOn &&
                this.hiddenAndNotPeeking[type][i] &&
                this.starredStates.words[i] &&
                this.numCorrect[type][i] < this.$store.state.options.exercisesKnownThreshold
            );
        },
        flipAnswer: function(deltas, type, i) {
            if (deltas[i] <= 0) deltas[i] = 1;
            else deltas[i] = -1;
            const input = type === 'py'? this.pyInputs[i].input : this.trInputs[i].input;
            if (deltas[i] > 0) {
                const hz = this.wordData.hz[i];
                const pyDiacritical = this.wordData.py[i].toLowerCase();
                const key = `${hz}-${pyDiacritical}-${type}`;
                let translations = this.$store.state.options.personalExerciseTranslations[key];
                if (translations) {
                    translations.push(input);
                }
                else {
                    translations = [input];
                }

                this.$store.commit('setDeepOption', {key: 'personalExerciseTranslations', key2: key, value: translations});
                this.$q.notify({
                    type: 'positive',
                    message: 'Overridden as correct',
                    position: 'top',
                });
            }
            this.applyAnswer(deltas[i], input, type, i);
        },
        getChars: function(ops) {
            let chars = [];
            for (const op of ops) {
                if (op.type == 1) {
                    chars.push([op.from_seq[op.from_idx], 'delete']);
                }
                if (op.type == 2) {
                    chars.push([op.to_seq[op.to_idx], 'insert']);
                }
                if (op.type == 3) {
                    if (op.delta >= 1) {
                        chars.push([op.to_seq[op.to_idx], 'badmiss']);
                    }
                    else if (op.delta > 0) {
                        chars.push([op.to_seq[op.to_idx], 'nearmiss']);
                    }
                    else {
                        chars.push([op.from_seq[op.from_idx], 'substitute']);
                    }
                }
            }
            return chars;
        },
        onPyInputEnter: function(idx) {
            const result = weightedLevenshtein(this.pyInputs[idx], this.wordData.py[idx], function(a, b) {
                if (a === b || a.toLowerCase() === b.toLowerCase()) return 0.0
                else if (removeDiacriticals(a) === removeDiacriticals(b)) {
                    return 0.5;
                }
                return 1.0;
            }, null, null, true);

            const input = this.pyInputs[idx];
            this.pyInputs[idx] = {
                distance: result.distance,
                chars: this.getChars(result.ops),
                input: input,
                target: this.wordData.py[idx],
            };
            let delta = null;
            if (result.distance === 0) delta = 1;
            else if (result.distance <= 1) delta = 0;
            else delta = -1;
            this.pyInputSubmitted[idx] = delta;
            this.updateSubmittedExercises();
            this.onInputTab('py', idx);
            this.applyAnswer(delta, input, 'py', idx);
            this.lastAnswerCorrect = delta > 0;
            if (delta < 0 && ! this.$store.state.options.seenTooltips.grading) {
                this.showPinyinGradingTooltip = true;
                this.showTooltipIdx = idx;
                this.$store.commit('setDeepOption', {key: 'seenTooltips', key2: 'grading', value: true});
            }
        },
        onTrInputEnter: function(idx) {
            const hz = this.wordData.hz[idx];
            const py = this.wordData.pys[idx].join('').toLowerCase();
            const pyDiacritical = this.wordData.py[idx].toLowerCase();
            const cedictEntries = this.$store.state.DICT[hz] || [];
            let cedictTranslations = [];
            for (let entry of cedictEntries) {
                entry = dictArrayToDict(entry);
                const entryPy = entry.pys.join('').toLowerCase();
                if (entryPy === py) {
                    cedictTranslations = cedictTranslations.concat(entry.translations)
                }
            }
            const showDictEntries = this.$store.state.SHOWS_DICTIONARY[hz] || [];
            const showDictTranslations = showDictEntries[pyDiacritical] || [];
            const personalExerciseTranslations = this.$store.state.options.personalExerciseTranslations[`${hz}-${pyDiacritical}-tr`] || [];
            let possibleTranslations = cedictTranslations.concat(showDictTranslations).concat(personalExerciseTranslations);
            possibleTranslations.push(this.wordData.tr[idx]);
            const possibleTranslationsWithoutStopWords = [];
            for (const translation of possibleTranslations) {
                const translationWithoutStopWords = filterStopWords(translation);
                if (translationWithoutStopWords !== translation) possibleTranslationsWithoutStopWords.push(translationWithoutStopWords);
            }

            possibleTranslations = possibleTranslations.concat(possibleTranslationsWithoutStopWords);

            let minResult = null;
            for (const translation of possibleTranslations) {
                const result = weightedLevenshtein(this.trInputs[idx], translation, function(a, b) {
                    return a === b || a.toLowerCase() === b.toLowerCase() ? 0.0 : 1.0;
                }, null, null, true);

                if (minResult === null || result.distance < minResult.distance) {
                    minResult = result;
                    minResult.target = translation;
                }
            }

            const input = this.trInputs[idx];
            this.trInputs[idx] = {
                distance: minResult.distance,
                chars: this.getChars(minResult.ops),
                input: input,
                target: minResult.target,
            };
            const distanceRatio = minResult.distance / minResult.target.length;
            console.log('distanceRatio', distanceRatio);
            const delta = distanceRatio <= this.$store.state.options.trExerciseDistanceRatioThreshold ? 1 : -1;
            this.trInputSubmitted[idx] = delta;
            this.updateSubmittedExercises();
            this.onInputTab('tr', idx);
            this.applyAnswer(delta, input, 'tr', idx);
            this.lastAnswerCorrect = delta > 0;
            if (delta < 0 && ! this.$store.state.options.seenTooltips.grading) {
                this.showTranslationGradingTooltip = true;
                this.showTooltipIdx = idx;
                this.$store.commit('setDeepOption', {key: 'seenTooltips', key2: 'grading', value: true});
            }
        },
        updateSubmittedExercises: function() {
            this.$store.commit('setSubmittedExercises', {
                playerId: this.playerId,
                key: this.currentCaptionIdx,
                value: {
                    'pyInputSubmitted': deepCopy(this.pyInputSubmitted),
                    'trInputSubmitted': deepCopy(this.trInputSubmitted),
                    'pyInputs': deepCopy(this.pyInputs),
                    'trInputs': deepCopy(this.trInputs),
                },
            });
        },
        onInputTab: function(currentType = null, currentIdx = 0) {
            const numWords = this.starredStates.words.length;
            for (let i = currentIdx % numWords; i < numWords; i++) {
                if (!this.starredStates.words[i]) continue;

                let found = false;
                for (const type of ['py', 'tr']) {
                    if (i === currentIdx && type === currentType) continue;
                    const key = `${type}Input_${i}`;
                    const $el = this.$refs[key];
                    if ($el) {
                        $el.focus();
                        found = true;
                        break;
                    }
                }

                if (found) break;
            }
        },
        mouseMove: function() {
            for (let i = 0; i < this.mouseHasNotMovedAfterPeeking.length; i++) {
                this.mouseHasNotMovedAfterPeeking[i] = false;
            }
        },
        showPinRow: function(type) {
            return !this.$store.state.options.pin[type];
        },
        getClasses: function(type, i, isPeekRow = false) {
            const cl = {
                captioncard: true,
                peeking: i !== null && this.purePeekStates[type][i],
                captioncardhidden: i !== null && this.hiddenAndNotPeeking[type][i],
                nonhanzi: i !== null && this.wordData.pys[i] === null,
                starred: i !== null && this.starredStates.words[i],
                hiddenstate: i !== null && this.hiddenStates[type][i],
                peekrow: i === null,
                pinned: this.$store.state.peekStates.rows[type],
                nonhanzirow: type !== 'hz' && ! isPeekRow,
                mousehasnotmovedafterpeeking: this.mouseHasNotMovedAfterPeeking[i],
            };
            return cl;
        },
        stateKey: function(type, i = null) {
            return wordDataStateKey(this.wordData, type, i);
        },
        clickPeekRow: function(type) {
            this.$store.commit('setPeekState', {'type': type, value: true});
            this.appendSessionLog([getEvent('peek_row', type)]);
        },
        clickRowContextMenu(action, type) {
            this.videoAPI.pause();

            if (action === 'copy') {
                if (type === 'translation') {
                    updateClipboard(this.wordData[type], 'Copied to clipboard');
                }
                else if (type === 'py') {
                    updateClipboard(this.wordData.py.join(' '), 'Copied to clipboard');
                }
                else if (type === 'hz') {
                    updateClipboard(this.wordData.text, 'Copied to clipboard');
                }
                return;
            }
            else if (action === 'options') {
                this.$store.commit('setShowDialog', {dialog: 'options', value: true});
                return;
            }

            this.$store.commit('setDeepOption', {key: 'pin', key2: type, value: action === 'pin'});
            this.appendSessionLog([getEvent('pin_row', type), action === 'pin']);
            if (action === 'pin') {
                this.$store.commit('setPeekState', {'type': type, value: true});
                this.appendSessionLog([getEvent('peek_row', type)]);
            }
        },
        clickContextMenu(action, type, i) {
            this.videoAPI.pause();
            if (action === 'star') {
                let content = '';
                if (type === 'translation') content = this.wordData.translation;
                else {
                    content = `${this.wordData.hz[i]}/${this.wordData.py[i]}`;
                }

                // Star and hide
                this.applyState(type, i, StateStarred, StateStarred);
                this.applyState(type, i, StateHidden, StateHidden);
                // Peek hz
                this.$store.commit('setPeekState', {'type': 'hz', 'i': i, value: true});
                // Focus the input
                const self = this;
                this.$nextTick(function () {
                    self.$refs[`pyInput_${i}`].focus();
                });
                if (! this.$store.state.options.seenTooltips.pinyin) {
                    this.showPinyinTooltip = true;
                    this.showTooltipIdx = i;
                    this.$store.commit('setDeepOption', {key: 'seenTooltips', key2: 'pinyin', value: true});
                }

                self.$q.notify({
                    type: 'positive',
                    message: `"${content}" added`,
                    position: 'top',
                    actions: [
                        { label: 'Open words', color: 'white', handler: function() { self.$store.commit('setPage', 'words'); } }
                    ]
                });
            }
            else if (action === 'unstar') {
                this.applyState(type, i, StateStarred, StateNone);
            }

            if (action === 'dict') {
                let [startIdx, endIdx, ...rest] = this.data.alignments[i];
                this.$store.commit('setShowDictionary', {value: true, range: [startIdx, endIdx], playerId: this.playerId});
            }
            else if (action === 'copy') {
                if (type === 'translation') {
                    updateClipboard(this.wordData[type], 'Copied to clipboard');
                }
                else {
                    const text = `${this.wordData.hz[i]}-${this.wordData.py[i]}-${this.wordData.tr[i]}`;
                    updateClipboard(text, 'Copied to clipboard');
                }
            }
            else if (action === 'switch') {
                this.$store.commit('switchTranslation');
            }
        },
        applyAnswer: function(delta, answer, type, i) {
            if (delta === 0) return;

            const k = this.$store.state.states;
            const pys = i === null ? null : this.wordData.pys[i];
            const hz = i === null ? null : this.wordData.hz[i];
            const tr = i === null ? null : this.wordData.tr[i];

            updateCorrect(delta, k, type, hz, pys, tr, true);
            const idx = this.data.origIdx || this.currentCaptionIdx;
            this.appendSessionLog([getEvent('answer', type), hz, pys, tr, delta, idx, answer]);
        },
        applyState: function(type, i, stateType, setState) {
            const d = this.$store.state.DICT;
            const k = this.$store.state.states;

            const pys = i === null ? null : this.wordData.pys[i];
            const hz = i === null ? null : this.wordData.hz[i];
            const tr = i === null ? null : this.wordData.tr[i];

            applyState(d, k, type, hz, pys, tr, this.wordData.translation, stateType, setState, true, true);
            let action = '';
            if (stateType === StateHidden) {
                action = setState === StateHidden ? 'hide' : 'pin';
            }
            else if (stateType === StateStarred) {
                action = setState === StateStarred ? 'star' : 'unstar';
            }
            const eventData = [getEvent(action, type), i];
            if (setState === StateStarred) {
                eventData.push(this.getCurrentState());
            }
            this.appendSessionLog(eventData);
        },
        getCurrentState: function() {
            // We add dt so that we can uniquely identify this event state
            const dt = Date.now() - this.sessionTime;
            const idx = this.data.origIdx || this.currentCaptionIdx;
            return {
                data: this.data,
                translationIdx: this.translationIdx,
                hidden: this.hiddenStates,
                dt: dt,
                captionIdx: idx,
            };
        },
        click: function(type, i = null) {
            // type in ['hz', 'translation']

            if (this.showExercise('py', i) || this.showExercise('tr', i)) {
                return;  // don't want to do anything on this word if we're having an exercise
            }

            this.videoAPI.pause();
            if (type === 'translation') {
                if (this.hiddenAndNotPeeking[type] === true) {
                    this.$store.commit('setPeekState', {'type': type, 'i': i, value: true});
                    this.applyState(type, i, StateHidden, StateNone);
                }
                return;
            }

            if (this.wordData.pys[i] === null || this.mouseHasNotMovedAfterPeeking[i]) {
                this.mouseHasNotMovedAfterPeeking[i] = false;
                return;
            }

            if (this.hiddenStates[type][i]) {
                let peekValue = null;
                if (this.$store.state.peekStates[type][i]) {
                    this.applyState('word', i, StateHidden, StateNone); // Pin it
                    peekValue = false;
                }
                else {
                    this.appendSessionLog([getEvent('peek', 'word'), i]);
                    peekValue = true;
                    this.mouseHasNotMovedAfterPeeking[i] = true;
                }

                this.$store.commit('setPeekState', {'type': 'hz', 'i': i, value: peekValue});

                // Only peek py/tr if we're not having an exercise here
                if (! (this.showExercise('py', i) || this.showExercise('tr', i))) {
                    for (const t of ['py', 'tr']) {
                        this.$store.commit('setPeekState', {'type': t, 'i': i, value: peekValue});
                    }
                }
            }
            else {
                this.applyState('word', i, StateHidden, StateHidden); // Hide it
            }
        },
        isHiddenStoreOrLvlStates: function(type, hz, pys) {
            const key = getStateKey(type, hz, pys, null, null);
            return (
                getState(this.hideWordsLevelStates, key, StateHidden, StateNone) === StateHidden ||
                getState(this.$store.state.states, key, StateHidden, StateNone) === StateHidden
            );
        },
        autoHideWord: function(i) {
            this.appendSessionLog([getEvent('hide_auto', 'word'), i]);
        },
        applyPersonalKnownVocab: function() {
            const d = this.$store.state.DICT;
            const personalKnownVocabulary = this.$store.state.options.personalKnownVocabulary;
            const k = this.$store.state.states;
            if (isNone(d) || isNone(k) || isNone(personalKnownVocabulary)) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.pys[i] === null ? '' : this.wordData.hz[i];
                if (hz.length === 0) continue;
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                const key = this.stateKey('word', i);
                if (
                    getState(k, key, StateHidden, null) === null &&
                    (
                        getState(this.personalKnownVocabularyStates, key, StateHidden, StateNone) === StateHidden
                    )
                ) {
                    console.log('PERSONAL VOCAB: Marking', 'word', hz, pys, tr, 'as hidden');
                    this.autoHideWord(i);
                    applyState(d, k, 'word', hz, pys, tr, this.wordData.translation, StateHidden, StateHidden, true, true);
                }
            }
        },
        applyLvlStates: function() {
            const d = this.$store.state.DICT;
            const k = this.$store.state.states;
            if (isNone(d) || isNone(k)) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.pys[i] === null ? '' : this.wordData.hz[i];
                if (hz.length === 0) continue;
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                const key = this.stateKey('word', i);
                if (
                    getState(k, key, StateHidden, null) === null &&
                    (
                        getState(this.hideWordsLevelStates, key, StateHidden, StateNone) === StateHidden ||
                        this.$store.state.options.hideWordsLevel === 7 || // all
                        ( // Any number + MW should be hidden if hide level is > 2
                            hz.match(CHINESE_NUMBERS_REGEX) &&
                            this.$store.state.options.hideWordsLevel > 2
                        )
                    )
                ) {
                    console.log('LVLS: Marking', 'word', hz, pys, tr, 'as hidden');
                    this.autoHideWord(i);
                    applyState(d, k, 'word', hz, pys, tr, this.wordData.translation, StateHidden, StateHidden, true, true);
                }
            }
        },
        applyPinnedRows: function() {
            for (const type of ['translation', 'py', 'hz', 'tr']) {
                if (this.$store.state.options.pin[type]) {
                    this.$store.commit('setPeekState', {'type': type, value: true});
                    this.appendSessionLog([getEvent('peek', type)]);
                }
            }
        },
        applyComponents: function() {
            // If user hides 你好, we should hide 你 and 好 separately, but not other way around.

            const d = this.$store.state.DICT;
            const k = this.$store.state.states;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.hz[i];
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];

                const key = getStateKey('word', hz, pys, null, null);
                const currState = getState(k, key, StateHidden, StateNone);

                if (d[hz] !== undefined || pys === null || isName(tr) || currState !== StateHidden) continue;

                let words = [];
                for (let w = 5; w >= 1; w--) {
                    for (let startIdx = 0; startIdx < hz.length-w+1; startIdx++) {
                        const endIdx = startIdx + w;
                        const hzSub = hz.substring(startIdx, endIdx);
                        const pysSub = pys.slice(startIdx, endIdx);
                        if (hzSub === hz) continue;
                        if (d[hzSub] === undefined) continue;

                        console.log('applyComponents: ', 'word', hzSub, pysSub);
                        applyState(d, k, 'word', hzSub, pysSub, tr, this.wordData.translation, StateHidden, StateHidden, false, true);
                    }
                }
            }
        },
        applyCompoundWordsNotInDict: function() {
            // If word is not in dict, but we hide all the sub-words, then we say we hide the compound
            // The reasoning is, if it's not in the dictionary, it's more likely to be a compound of regular words that
            // have a similar meaning to the parts. If it had a very different meaning, then it should be in the dictionary.
            const d = this.$store.state.DICT;
            const k = this.$store.state.states;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.hz[i];
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                if (d[hz] !== undefined || pys === null || isName(tr)) continue;

                const taken = [];
                for (let j = 0; j < hz.length; j++) taken.push(false);

                let words = [];
                for (let w = 5; w >= 1; w--) {
                    for (let startIdx = 0; startIdx < hz.length-w+1; startIdx++) {
                        const endIdx = startIdx + w;
                        if (taken.slice(startIdx, endIdx).includes(true)) continue;

                        const hzSub = hz.substring(startIdx, endIdx);
                        if (d[hzSub] === undefined) continue;

                        for (let k = 0; k < w; k++) taken[startIdx+k] = true;
                        words.push([hzSub, pys.slice(startIdx, endIdx)]);
                    }
                }

                let allHidden = true;
                for (const [wordHz, wordPys] of words) {
                    allHidden = allHidden && this.isHiddenStoreOrLvlStates('word', wordHz, wordPys);
                }

                if (getState(k, this.stateKey('word', i), StateHidden, StateNone) === StateHidden) {
                    continue;
                }

                if (allHidden) {
                    console.log('applyCompoundWordsNotInDict', 'word', hz, pys);
                    this.autoHideWord(i);
                    applyState(d, k, 'word', hz, pys, tr, null, StateHidden, StateHidden, false, true);
                }
            }
        },
        applySimpleCompounds: function() {
            // IMPORTANT: any changes here will have to be reflected in make_shows_list.py

            if (this.$store.state.SIMPLE_CHARS === null) return;
            // Where there is a main component, and an additional "simple" character like 了
            // For example, 地上, 拿不着, 这样的, 不服气, 知道了, middle chars: 离不开, 想不到

            const simpleCharsPrePost = this.$store.state.SIMPLE_CHARS.pre_post;
            const simpleCharsPre = this.$store.state.SIMPLE_CHARS.pre.concat(simpleCharsPrePost);
            const simpleCharsMiddle = this.$store.state.SIMPLE_CHARS.middle;
            const simpleCharsPost = this.$store.state.SIMPLE_CHARS.post.concat(simpleCharsPrePost);

            const d = this.$store.state.DICT;
            const k = this.$store.state.states;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.hz[i];
                if (hz.length < 2) continue;

                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                if (pys === null || isName(tr)) continue; // non hanzi or name

                let allHidden = false;
                if (getState(k, this.stateKey('word', i), StateHidden, StateNone) === StateHidden) {
                    allHidden = true;
                }

                for (let middleIdx = 1; middleIdx < hz.length; middleIdx++) {
                    const preHz = hz.substring(0, middleIdx);
                    const postHz = hz.substring(middleIdx);
                    const prePys = pys.slice(0, middleIdx);
                    const postPys = pys.slice(middleIdx, pys.length);

                    let preIsHidden = this.isHiddenStoreOrLvlStates('word', preHz, prePys);
                    let postIsHidden = this.isHiddenStoreOrLvlStates('word', postHz, postPys);
                    let preIsSimple = simpleCharsPre.includes(preHz) || preHz.match(CHINESE_NUMBERS_REGEX) !== null;
                    let postIsSimple = simpleCharsPost.includes(postHz) || postHz.match(CHINESE_NUMBERS_REGEX) !== null;

                    let isSimpleCompound = (preIsHidden && postIsSimple) || (preIsSimple && postIsHidden);

                    allHidden = allHidden || isSimpleCompound;
                }

                for (const middleChar of simpleCharsMiddle) {
                    if (! hz.substring(1, hz.length-1).includes(middleChar)) continue;

                    const middleIdx = hz.indexOf(middleChar);
                    const prePostHz = hz.substring(0, middleIdx) + hz.substring(middleIdx + 1);
                    const prePostPys = pys.slice(0, middleIdx).concat(pys.slice(middleIdx + 1));
                    allHidden = allHidden || this.isHiddenStoreOrLvlStates('word', prePostHz, prePostPys);
                }

                if (allHidden) {
                    if (getState(k, this.stateKey('word', i), StateHidden, null) === null) {
                        console.log('applySimpleCompounds', 'word', hz, pys);
                        this.autoHideWord(i);
                        applyState(d, k, 'word', hz, pys, tr, null, StateHidden, StateHidden, false, true);
                    }
                }
            }
        }
    }
};
</script>

<style>

.peekrow {
    width: 25px;
}

.captioncontent {
    font-family: 'Heiti SC';
    display: inline-block;
    padding-left: 0.25em !important;
    padding-right: 2em !important;
    padding-bottom: 0.5 !important;
    opacity: 1;
    text-align: left;
}

.fadeout .captioncontent {
    opacity: 0;
    visibility: hidden;
    transition: visibility 0s 1.5s, opacity 1.5s linear;
}

.contenttable {
    color: white;
    font-size: 30px;
    display: inline-block;
    text-align: center;
    table-layout: fixed;
    border-spacing: 10px 0em;
    font-family: sans-serif;
}

.contenttable.extrapaddingtop {
    padding-top: 10px;
}

.contenttable.extrapaddingbottom {
    padding-bottom: 10px;
}

.contenttable tr {
    line-height: 1.0em;
}

.contenttable.plain {
    margin-top: 10px;
    margin-bottom: 10px;
}

.toprow td:not(:first-child) span {
    font-size: 0.4em;
}

.centerrow td:not(:first-child) {
    line-height: 1.0em;
}

.centerrow td:not(:first-child) span {
    font-size: 1.0em;
}

.centerrow {
    vertical-align: bottom;
}

.bottomrow td:not(:first-child) span {
    font-size: 0.4em;
}

.captioncard {
    position: relative;
    white-space: nowrap;
    border: 1px solid transparent;
    border-radius: 5px;
}

.captioncard:not(.plainhz.peeking) {
    user-select: none;
}

.captioncard:not(.nonhanzi):not(.nonhanzirow):not(.plainhz.peeking) {
    cursor: pointer;
}

.captioncard:not(.nonhanzi):not(.nonhanzirow):not(.plainhz.peeking):not(.peekrow):hover {
    background-color: gray !important;
}

.captioncard:not(.nonhanzi):not(.nonhanzirow):not(.plainhz.peeking):not(.peekrow):active {
    background-color: lightgray !important;
}

.peekrow:hover .iconcard {
    background-color: gray !important;
}

.peekrow:active .iconcard {
    background-color: lightgray !important;
}


.captioncard:not(.fulltranslation) {
    padding-left: 2px;
    padding-right: 2px;
}

.centerrow .captioncardhidden:not(.nonhanzi):not(.peekrow):not(.mousehasnotmovedafterpeeking) {
    background-color: rgb(30, 30, 30);
}

.centerrow .plainhz:not(.peeking) {
    background-color: rgb(30, 30, 30);
}

.centerrow .captioncard {
    padding-top: 3px;
    padding-bottom: 3px;
}

.cardcontent {
    position: relative;
}

.captioncard.peeking:not(.fulltranslation):not(.pinned):not(.mousehasnotmovedafterpeeking) .cardcontent {
    color: rgb(170, 170, 170);
}

.captioncard.plainhz .cardcontent {
    color: white !important;
}

.captioncard.pinned.hiddenstate .cardcontent {
    color: rgb(160, 160, 160) !important;
}

.captioncard:not(.nonhanzi):not(.fulltranslation):not(.nonhanzirow:not(.captioncardhidden)):not(.plainhz.peeking):not(.mousehasnotmovedafterpeeking):hover .cardcontent {
    color: rgb(100, 100, 100) !important;
}

.mousehasnotmovedafterpeeking .cardcontent {
    cursor: none;
}

.peekrow .cardcontent {
    font-size: 12px;
    color: lightgray;
    position: absolute;
    line-height: 0;
    left: 0;
    top: 50%;
    width: 100%;
    margin-top: 0em;
}

.peekrow:hover .cardcontent {
    visibility: hidden;
}

.iconcard {
    position: absolute;
    line-height: 0;
    height: 20px;
    visibility: hidden;
    z-index: 999;
    border-radius: 3px;
}

.iconcard.peek {
    left: 0;
    top: 50%;
    width: 100%;
    margin-top: -10px;
}

.iconcard > svg {
    border-radius: 3px;
    padding: 2px;
}

.captioncard:hover:not(.nonhanzi) .iconcard,
.captioncard.fulltranslation .iconcard {
    cursor: pointer;
    visibility: visible;
}

.fulltranslationtable {
    display: block;
    margin-top: -4px;
    margin-bottom: 5px;
}

.fulltranslationtable tr {
    line-height: 0.8em;
}

.fulltranslation {
    margin-left: 2em;
    padding-top: 0.2em;
    padding-bottom: 0.2em;
    text-align: center;
}

.fulltranslation .cardcontent {
    font-size: 0.4em;
}

.fulltranslation.placeholder {
    color: gray;
}

.fulltranslation.placeholder:active {
    color: white;
}

.fulltranslation.placeholder:hover {
    color: white;
}

.fulltranslation > .cardcontent {
    padding-left: 0.3em;
    padding-right: 0.3em;
}

.captioncard:hover:not(.fulltranslation):not(.captioncardhidden) .starbadge {
    display: none !important;
}

.captioncardhidden .starbadge {
    display: none !important;
}

.captioncard .starbadge {
    margin-top: -6px;
    margin-right: -10px;
}

.starinput input {
    padding-top: 4px !important;
    padding-bottom: 4px !important;
    text-align: center;
    border-radius: 0.4em;
    box-shadow: 0 0 0 1px rgba(255, 165 , 0, .3);
}

.starinput input:focus {
    border-radius: 0.4em;
    box-shadow: 0 0 0 2px rgba(255, 165 , 0, 1.0);
}

.captioncontent .q-field__control {
    height: unset;
    font-size: unset;
}

.captioncontent .q-field {
    font-size: unset;
}

.insert {
    text-decoration: underline;
}

.substitute {
    color: lightgreen;
}

.nearmiss {
    color: orange;
    text-decoration: underline;
}

.badmiss {
    color: red;
    text-decoration: underline;
}

.delete {
    color: red;
    text-decoration: line-through;
    text-decoration: underline;
}

.captioncard .q-btn--round {
    min-height: 1.25em;
    min-width: 1.25em;
    margin-top: 3px;
    margin-left: 3px;
}

</style>
