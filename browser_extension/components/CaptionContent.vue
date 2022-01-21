<template>
    <div :class="{captioncontent: true, fadeout: fadeOut, notransition: showData !== null && showData.dummy === true }">
        <table class="contenttable">
            <tr class="toprow">
                <td
                    :class="{captioncard: true, peeking: peekStates['py'][i], captioncardhidden: !finalShowStates['py'][i] }"
                    @click="peek('py', i)"
                    v-for="(py, i) in pys"
                    :key="i"
                >
                    <span :style="{opacity: finalShowStates['py'][i] ? 1 : 0}">{{ finalShowStates['py'][i] ? py : '-' }}</span>
                    <span :style="{opacity: finalShowStates['py'][i] ? 0 : 1}" class="peekcard" v-html="eyecon"></span>
                </td>
            </tr>
            <tr class="centerrow">
                <td
                    :class="{captioncard: true, peeking: peekStates['hz'][i], captioncardhidden: !finalShowStates['hz'][i] }"
                    @click="peek('hz', i)"
                    v-for="(hz, i) in hzs"
                    :key="i"
                >
                    <span :style="{opacity: finalShowStates['hz'][i] ? 1 : 0}">{{ hz }}</span>
                    <span :style="{opacity: finalShowStates['hz'][i] ? 0 : 1}" class="peekcard" v-html="eyecon"></span>
                </td>
            </tr>
            <tr class="bottomrow">
                <td
                    :class="{captioncard: true, peeking: peekStates['tr'][i], captioncardhidden: !finalShowStates['tr'][i] }"
                    @click="peek('tr', i)"
                    v-for="(tr, i) in trs"
                    :key="i"
                >
                    <span
                        :title="finalShowStates['tr'][i] && tr !== null && tr.length > truncateTrLengths[i] ? tr : null"
                        :style="{opacity: finalShowStates['tr'][i] ? 1 : 0}"
                    >
                        {{ tr !== null && finalShowStates['tr'][i] ? (tr.substring(0, truncateTrLengths[i]) + (tr.length > truncateTrLengths[i] ? '...' : '')) : '-' }}
                    </span>
                    <span :style="{opacity: finalShowStates['tr'][i] ? 0 : 1}" class="peekcard" v-html="eyecon"></span>
                </td>
            </tr>
        </table>
        <div
            @click="peek('translation')"
            :class="{
                captioncard: true,
                peeking: peekStates['translation'],
                fulltranslation: true,
                placeholder: !finalShowStates['translation'],
                showborder: showData !== null,
            }"
        >
            {{ translation }}
        </div>
    </div>
</template>
<script>
export default {
    props: {
        data: { default: null },
        currTime: { default: null },
    },
    data: function () { return {
        showData: this.data,
        fadeOut: false,  // NOTE: we set fadeOut based on currTime in a watch instead of computed, because a computed makes the component re-render every frame
        eyecon: getIconSvg("eye", 18),
    }},
    computed: {
        peekStates: function() {
            const states = this.$store.state.peekStates;
            states['translation'] = states['translation'] && !this.showStates['translation'];
            for (var i = 0; i < this.hzs.length; i++) {
                states['py'][i] = states['py'][i] && !this.showStates['py'][i];
                states['hz'][i] = states['hz'][i] && !this.showStates['hz'][i];
                states['tr'][i] = states['tr'][i] && !this.showStates['tr'][i];
            }
            return states;
        },
        truncateTrLengths: function() {
            let outLengths = [];
            for (let i = 0; i < this.showData.alignments.length; i++) {
                const trunateLength = Math.max(15, Math.ceil(Math.max(this.pys[i].length, this.hzs[i].length) * 2))  // add 100% to longest
                outLengths.push(trunateLength);
            }
            return outLengths;
        },
        translation: function() {
            if (this.showData == null) return '';
            if (this.finalShowStates['translation']) return this.showData.translations[0];
            return '...';
        },
        text: function() { return this.showData.texts.join(' '); },
        hzs: function() { return this.hzsPysTrsIndices.hzs; },
        pys: function() { return this.hzsPysTrsIndices.pys; },
        trs: function() { return this.hzsPysTrsIndices.trs; },
        alignmentIndices: function() { return this.hzsPysTrsIndices.alignments; },
        hzsPysTrsIndices: function() {
            if (this.showData === null) {
                return {hzs: [], pys: [], trs: [], alignments: []};
            }

            let nextIdx = 0;
            let hanzis = [];
            let pinyins = [];
            let translations = [];
            let alignmentIndices = [];
            for (let i = 0; i < this.showData.alignments.length; i++) {
                let [startIdx, endIdx, _, pinyinParts, wordTranslation] = this.showData.alignments[i];
                if (startIdx > nextIdx) {
                    hanzis.push(this.text.substring(nextIdx, startIdx));
                    pinyins.push(null);
                    translations.push(null);
                    alignmentIndices.push(null);
                }
                const hz = this.text.substring(startIdx, endIdx);
                hanzis.push(hz);
                const diacriticalPinyins = pinyinParts.map((part) => part[0]);
                const displayPinyin = diacriticalPinyins.join('');
                pinyins.push(displayPinyin);
                translations.push(wordTranslation);
                alignmentIndices.push(i);
                nextIdx = endIdx;
            }
            if (nextIdx < this.text.length) {
                hanzis.push(this.text.substring(nextIdx, this.text.length));
                pinyins.push(null);
                translations.push(null);
            }
            return {hzs: hanzis, pys: pinyins, trs: translations, alignments: alignmentIndices};
        },
        showStates: function() {
            const states = {'py': [], 'hz': [], 'tr': [], 'translation': false};
            for (let i = 0; i < this.hzs.length; i++) {
                const hz = this.hzs[i];
                const py = this.pys[i];
                const tr = this.trs[i];
                for (var type of ['hz', 'py', 'tr']) {
                    const isUnknown = this.$store.getters.getKnowledgeState(this.knowledgeKey(type, hz, py, tr)) === KnowledgeUnknown;
                    states[type].push(isUnknown);
                }
            }
            return states;
        },
        finalShowStates: function() {
            const states = {'py': [], 'hz': [], 'tr': [], 'translation': this.showStates['translation'] || this.peekStates['translation']};
            for (let i = 0; i < this.hzs.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = this.showStates[type][i] || this.peekStates[type][i];
                }
            }
            return states;
        },
    },
    watch: {
        data: {
            immediate: true,
            handler: function(newData, oldData) {
                if (newData !== null) {
                    this.showData = newData;
                }
                if (newData !== oldData) {
                    if (newData !== null && newData.dummy === true) return;
                    this.applyKnownHSKLevels();
                    this.applyKnownCompounds();
                    this.updateFadeout();

                    const pyPeekStates = [];
                    const hzPeekStates = [];
                    const trPeekStates = [];
                    for (let i = 0; i < this.hzs.length; i++) {
                        pyPeekStates.push(false);
                        hzPeekStates.push(false);
                        trPeekStates.push(false);
                    }
                    this.$store.commit('setPeekStates', {
                        'py': pyPeekStates,
                        'hz': hzPeekStates,
                        'tr': trPeekStates,
                        'translation': false
                    });
                }
            },
        },
        currTime: {
            immediate: true,
            handler: function(newTime, oldTime) {
                if (newTime !== oldTime) {
                    this.updateFadeout();
                }
            },
        },
    },
    methods: {
        updateFadeout: function() {
            this.fadeOut = this.showData !== null && (this.currTime > this.showData.t1 + CAPTION_FADEOUT_TIME || this.currTime < this.showData.t0); // eslint-disable-line
        },
        resolveTypeIdx: function(type, idx) {
            if (type === 'hz') return this.hzs[idx];
            if (type === 'py') return this.pys[idx];
            if (type === 'tr') return this.trs[idx];
        },
        knowledgeKey: function(type, hz, py, tr) {
            let key = null;
            if (type == 'hz') key = `hz-${hz}`;
            if (type == 'py') key = `py-${hz}-${py}`;
            if (type == 'tr') key = `tr-${hz}-${py}`;
            if (type == 'translation') key = `tr-${hz}`;
            return key;
        },
        peek: function(type, i = null) {
            this.$store.commit('setPeekState', {'type': type, 'i': i});
        },
        /*
        clickKey: function(key, defaultValue = true) {
            if (this.$store.getters.getKnowledgeState(key) === undefined) {
                this.$store.commit('setKnowledgeKey', {'key': key, 'val': ! defaultValue});
            }
            else {
                this.$store.commit('setKnowledgeKey', {'key': key, 'val': ! this.$store.getters.getKnowledgeState(key)});
            }
        },
        clickIdx: function(type, i) {
            this.clickKey(this.knowledgeKey(type, this.hzs[i], this.pys[i], this.trs[i]));
        },
        clickTranslation: function() {
            this.clickKey(this.knowledgeKey('full', this.text, null, null));
        },
        clickTop: function(event, i) {
            this.clickIdx('py', i);
        },
        clickCenter: function(event, i) {
            this.clickIdx('hz', i);
        },
        clickBottom: function(event, i) {
            this.clickIdx('tr', i);
        },
        */
        setKnown: function(key, known) {
            this.$store.commit('setKnowledgeKey', {'key': key, 'val': known});
        },
        setKnownBatch: function(keys, vals) {
            this.$store.commit('setKnowledgeKeys', {'keys': keys, 'vals': vals});
        },
        applyKnownHSKLevels: function() {
            let keys = [];
            let vals = [];
            for (let i = 0; i < this.hzs.length; i++) {
                const hz = this.pys[i] === '' ? '' : this.hzs[i];
                if (hz.length === 0) continue;
                const py = this.pys[i] === '' ? this.hzs[i] : this.pys[i];
                const tr = this.trs[i];
                const hzKey = `hz-${hz}`;
                const pyKey = `py-${hz}-${py}`;
                let trKey = `tr-${hz}-${py}`;
                if (tr !== null && /[A-Z]/.test(tr.charAt(0)) && !(tr.startsWith('I') || tr.startsWith("I'"))) {
                    // If the translation is capitalized, we want it to be tracked separately
                    trKey = `tr-${hz}-${py}-${tr}`;
                }
                let wordLevel = getWordLevel(hz); // eslint-disable-line
                if (wordLevel !== null) {
                    if (this.$store.getters.getKnowledgeState(hzKey) === KnowledgeUnknown && wordLevel <= this.$store.state.options.hanziKnowLevel) {
                        keys.push(hzKey);
                        vals.push(KnowledgeKnown);
                    }

                    if (this.$store.getters.getKnowledgeState(pyKey) === KnowledgeUnknown && wordLevel <= this.$store.state.options.pinyinKnowLevel) {
                        keys.push(pyKey);
                        vals.push(KnowledgeKnown);
                    }

                    if (this.$store.getters.getKnowledgeState(trKey) === KnowledgeUnknown && wordLevel <= this.$store.state.options.translationKnowLevel) {
                        keys.push(trKey);
                        vals.push(KnowledgeKnown);
                    }
                }
            }
            this.setKnownBatch(keys, vals);
        },
        applyKnownCompounds: function() {
            // For pinyins, if all the pinyins of all the characters of a word are known, we mark the whole pinyin as known
        },
    }
};
</script>

<style>
.captioncontent {
    display: inline-block;
    padding-left: 2em !important;
    padding-right: 2em !important;
    padding-bottom: 0.5em !important;
    opacity: 1;
}

.captioncontent.fadeout {
    opacity: 0;
    visibility: hidden;
    transition: visibility 0s 1.5s, opacity 1.5s linear;
}

.captioncontent.fadeout.notransition {
    transition: none !important;
}

.contenttable {
    text-align: center;
    table-layout: fixed;
    border-spacing: 0.3em;
}

.toprow {
    font-size: 1em;
    font-family: sans-serif;
}

.centerrow {
    font-size: 1.25em;
    font-family: sans-serif;
    line-height: 1.25em;
    vertical-align: bottom;
}

.bottomrow {
    font-size: 0.8em;
    font-family: sans-serif;
}

.captioncard {
    position: relative;
    -webkit-user-select: none; /* Safari */
    -moz-user-select: none; /* Firefox */
    -ms-user-select: none; /* IE10+/Edge */
    user-select: none; /* Standard */
    white-space: nowrap;
    border: 1px solid black;
    border-radius: 5px;
}

.captioncard:not(.peeking) {
    cursor: pointer;
}

.captioncard:not(.peeking):hover {
    background-color: gray;
}

.captioncard:not(.peeking):active {
    background-color: lightgray;
}

.captioncard.peeking {
    color: rgb(169,169,169);
    padding-left: 2px;
    padding-right: 2px;
}

.captioncardhidden {
    line-height: 18px; /* NOTE: same as eye icon size */
}

.centerrow .captioncardhidden {
    border: 1px dashed white;
    line-height: 1.25em;
}

.peekcard {
    position: absolute;
    width: 100%;
    left: 0;
    visibility: hidden;
}

.captioncard:hover .peekcard {
    visibility: visible;
}

.fulltranslation {
    padding-top: 0.2em;
    padding-bottom: 0.2em;
    text-align: center;
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
</style>
