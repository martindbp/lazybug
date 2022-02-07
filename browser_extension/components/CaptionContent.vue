<template>
    <div :class="{captioncontent: true, fadeout: fadeOut, notransition: data !== null && data.dummy === true }">
        <table class="contenttable">
            <tr class="toprow">
                <td title="Peek pinyin row" :class="getClasses('py', null)" @click="peekAll('py')">
                    <span class="iconcard peek" v-html="eyecon"></span>
                    <span class="cardcontent">PY</span>
                </td>
                <td
                    :class="getClasses('py', i)"
                    @click="click('py', i)"
                    v-for="(py, i) in wordData.py"
                    :key="i"
                >
                    <span class="iconcard learn" title="Learn" v-html="bookIcon" v-if="peekStates.py[i] && knownStates.py[i]"></span>
                    <span class="iconcard know" title="Know this" v-html="checkIcon" v-if="showStates.py[i]"></span>
                    <span class="iconcard peek" v-html="eyecon" v-if="! finalShowStates.py[i]"></span>
                    <span class="iconcard remove" title="Reset" v-html="closeIcon" v-if="peekStates.py[i] && learningStates.py[i]"></span>
                    <span class="cardcontent" :style="{opacity: finalShowStates.py[i] ? 1 : 0}">{{ finalShowStates.py[i] ? py : '-' }}</span>
                </td>
            </tr>
            <tr class="centerrow">
                <td title="Peek hanzi row" :class="getClasses('hz', null)" @click="peekAll('hz')">
                    <span class="iconcard peek" v-html="eyecon"></span>
                    <span class="cardcontent">HZ</span>
                </td>
                <td
                    :class="getClasses('hz', i)"
                    @click="click('hz', i)"
                    v-for="(hz, i) in wordData.hz"
                    :key="i"
                >
                    <span class="iconcard learn" title="Learn" v-html="bookIcon" v-if="peekStates.hz[i] && knownStates.hz[i]"></span>
                    <span class="iconcard know" title="Know this" v-html="checkIcon" v-if="showStates.hz[i]"></span>
                    <span class="iconcard peek" v-html="eyecon" v-if="! finalShowStates.hz[i]"></span>
                    <span class="iconcard remove" title="Reset" v-html="closeIcon" v-if="peekStates.hz[i] && learningStates.hz[i]"></span>
                    <span class="cardcontent" :style="{opacity: finalShowStates.hz[i] ? 1 : 0}">{{ sm2tr(hz) }}</span>
                </td>
            </tr>
            <tr class="bottomrow">
                <td title="Peek word translation row" :class="getClasses('tr', null)" @click="peekAll('tr')">
                    <span class="iconcard peek" v-html="eyecon"></span>
                    <span class="cardcontent">TR</span>
                </td>
                <td
                    :class="getClasses('tr', i)"
                    @click="click('tr', i)"
                    v-for="(tr, i) in wordData.tr"
                    :key="i"
                >
                    <span class="iconcard learn" title="Learn" v-html="bookIcon" v-if="peekStates.tr[i] && knownStates.tr[i]"></span>
                    <span class="iconcard know" title="Know this" v-html="checkIcon" v-if="showStates.tr[i]"></span>
                    <span class="iconcard peek" v-html="eyecon" v-if="! finalShowStates.tr[i]"></span>
                    <span class="iconcard remove" title="Reset" v-html="closeIcon" v-if="peekStates.tr[i] && learningStates.tr[i]"></span>
                    <span
                        class="cardcontent"
                        :title="finalShowStates.tr[i] && tr !== null && tr.length > truncateTrLengths[i] ? tr : null"
                        :style="{opacity: finalShowStates.tr[i] ? 1 : 0}"
                    >
                        {{ tr !== null && finalShowStates.tr[i] ? (tr.substring(0, truncateTrLengths[i]) + (tr.length > truncateTrLengths[i] ? '...' : '')) : '-' }}
                    </span>
                </td>
            </tr>
        </table>
        <div
            @click="click('translation')"
            :class="{
                captioncard: true,
                peeking: peekStates['translation'],
                fulltranslation: true,
                placeholder: !finalShowStates['translation'],
                showborder: data !== null,
            }"
        >
            <span v-if="finalShowStates['translation']"> {{ translation }}</span>
            <span v-if="!finalShowStates['translation']" v-html="eyecon"></span>
        </div>
    </div>
</template>
<script>
import SvgButton from './SvgButton.vue'

export default {
    components: {
        SvgButton,
    },
    props: {
        data: { default: null },
        currTime: { default: null },
        fadeOut: { default: false },
    },
    data: function () { return {
        eyecon: getIconSvg("eye", 18),
        bookIcon: getIconSvg("study", 18),
        checkIcon: getIconSvg("check", 18),
        closeIcon: getIconSvg("undo", 18),
        undoIcon: getIconSvg("undo", 18),
    }},
    computed: {
        peekStates: function() {
            const states = this.$store.state.peekStates;
            states['translation'] = (states['translation'] || this.$store.state.options.show['fullTr']) && !this.showStates['translation'];
            for (var i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = (states[type][i] || this.$store.state.options.show[type]) && !this.showStates[type][i];
                }
            }
            return states;
        },
        truncateTrLengths: function() {
            let outLengths = [];
            for (let i = 0; i < this.data.alignments.length; i++) {
                const trunateLength = Math.max(15, Math.ceil(Math.max(this.wordData.py[i].length, this.wordData.hz[i].length) * 2))  // add 100% to longest
                outLengths.push(trunateLength);
            }
            return outLengths;
        },
        translation: function() {
            if (this.data == null) return '';
            return this.data.translations[0];
        },
        texts: function() {
            const sm = this.data.texts.join(' ');
            return {
                sm: sm,
                tr: this.sm2tr(sm),
            };
        },
        wordData: function() {
            const wordData = {hz: [], py: [], tr: [], translation: null, pys: [], pysDiacritical: []};
            if (this.data === null) {
                return wordData;
            }

            wordData.translation = this.data.translations[0];

            let nextIdx = 0;
            for (let i = 0; i < this.data.alignments.length; i++) {
                let [startIdx, endIdx, _, pyParts, wordTranslation] = this.data.alignments[i];
                if (startIdx > nextIdx) {
                    wordData.hz.push(this.texts.sm.substring(nextIdx, startIdx));
                    wordData.py.push('');
                    wordData.tr.push('');
                    wordData.pys.push(null);
                    wordData.pysDiacritical.push(null);
                }
                const hz = this.texts.sm.substring(startIdx, endIdx);
                wordData.hz.push(hz);
                const pysDiacritical = pyParts.map((part) => part[0]);
                const displayPinyin = pysDiacritical.join('');
                const pys = displayPinyin === '' ? null : pyParts.map((part) => part[1]);
                wordData.py.push(displayPinyin);
                wordData.tr.push(wordTranslation);
                wordData.pysDiacritical.push(pysDiacritical);
                wordData.pys.push(pys);
                nextIdx = endIdx;
            }
            if (nextIdx < this.texts.sm.length) {
                wordData.hz.push(this.texts.sm.substring(nextIdx, this.texts.sm.length));
                wordData.py.push('');
                wordData.tr.push('');
                wordData.pys.push(null);
                wordData.pysDiacritical.push(null);
            }
            //console.log('wordData', wordData);
            return wordData;
        },
        showStates: function() {
            const states = {'py': [], 'hz': [], 'tr': [], 'translation': false};
            for (let i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    const isUnknown = [KnowledgeUnknown, undefined].includes(
                        getKnowledgeState(this.$store.state.knowledge, this.knowledgeKey(type, i))
                    );
                    states[type].push(isUnknown);
                }
            }
            return states;
        },
        finalShowStates: function() {
            // Show states that include the peek states
            const states = {'py': [], 'hz': [], 'tr': [], 'translation': this.showStates['translation'] || this.peekStates['translation']};
            for (let i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = this.showStates[type][i] || this.peekStates[type][i];
                }
            }
            return states;
        },
        knownStates: function() {
            return this.getStates(KnowledgeKnown);
        },
        learningStates: function() {
            return this.getStates(KnowledgeLearning);
        },
    },
    watch: {
        data: {
            immediate: true,
            handler: function(newData, oldData) {
                if (newData !== oldData) {
                    if (newData !== null && newData.dummy === true) return;
                    this.applyKnownLvls();
                    this.applyKnownPinyinCompounds();

                    const allFalse = [];
                    for (let i = 0; i < this.wordData.hz.length; i++) {
                        allFalse.push(false);
                    }
                    this.$store.commit('setPeekStates', {
                        'py': allFalse.slice(),
                        'hz': allFalse.slice(),
                        'tr': allFalse.slice(),
                        'translation': false
                    });
                }
            },
        },
    },
    methods: {
        getClasses: function(type, i) {
            const cl = {
                captioncard: true,
                peeking: i !== null && this.peekStates[type][i],
                captioncardhidden: i !== null && ! this.finalShowStates[type][i],
                nonhanzi: i !== null && this.wordData.pys[i] === null,
                learning: i !== null && this.learningStates[type][i],
                known: i !== null && this.knownStates[type][i],
                peekall: i === null,
            };
            return cl;
        },
        getStates: function(compareTo) {
            const states = {'py': [], 'hz': [], 'tr': []};
            for (let i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    const state = getKnowledgeState(this.$store.state.knowledge, this.knowledgeKey(type, i));
                    states[type].push(state === compareTo);
                }
            }
            return states;
        },
        knowledgeKey: function(type, i) {
            return getKnowledgeKey(
                type,
                this.wordData.hz[i],
                this.wordData.pys[i],
                this.wordData.tr[i],
                this.wordData.translation
            );
        },
        click: function(type, i = null) {
            if (type === 'translation' && this.showStates[type] === false) {
                this.$store.commit('setPeekState', {'type': type, 'i': i});
                return;
            }

            if (this.wordData.pys[i] === null) return;

            const d = this.$store.state.DICT;
            const k = this.$store.state.knowledge;

            const pys = this.wordData.pys[i];
            const hz = this.wordData.hz[i];
            const tr = this.wordData.tr[i];
            if (this.showStates[type][i] === false) {
                if (! this.peekStates[type][i]) {
                    this.$store.commit('setPeekState', {'type': type, 'i': i});
                }
                else if (this.knownStates[type][i]) {
                    applyKnowledge(d, k, type, hz, pys, tr, this.wordData.translation, KnowledgeLearning);
                }
                else if (this.learningStates[type][i]) {
                    applyKnowledge(d, k, type, hz, pys, tr, this.wordData.translation, KnowledgeKnown);
                }
            }
            else {
                applyKnowledge(d, k, type, hz, pys, tr, this.wordData.translation, KnowledgeKnown);
                this.$store.commit('setPeekState', {'type': type, 'i': i});
            }
        },
        peek: function(type, i) {
            if (this.showStates[type][i] === false) {
                if (! this.peekStates[type][i]) {
                    this.$store.commit('setPeekState', {'type': type, 'i': i});
                }
            }
        },
        peekAll: function(type) {
            for (let i = 0; i < this.wordData.hz.length; i++) {
                this.peek(type, i);
            }
        },
        applyKnownLvls: function() {
            const d = this.$store.state.DICT;
            const k = this.$store.state.knowledge;
            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.pys[i] == null ? '' : this.wordData.hz[i];
                if (hz.length === 0) continue;
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                for (var type of ['hz', 'py', 'tr']) {
                    const key = this.knowledgeKey(type, i);
                    if (
                        [KnowledgeUnknown, undefined].includes(getKnowledgeState(k, key)) &&
                        getKnowledgeState(this.lvlKnowledge, key) == KnowledgeKnown
                    ) {
                        console.log('LVLS: Marking', type, hz, pys, tr, 'as known');
                        applyKnowledge(d, k, type, hz, pys, tr, this.wordData.translation, KnowledgeKnown);
                    }
                }
            }
        },
        applyKnownPinyinCompounds: function() {
            // For pinyins, if all the pinyins of all the characters of a word are known, we mark the whole pinyin as known
            // More specifically, the compound knowledge level is the minimum of the constituent parts
            const d = this.$store.state.DICT;
            const k = this.$store.state.knowledge;
            for (let i = 0; i < this.wordData.hz.length; i++) {
                let hasUnknown = false;
                let hasLearning = false;
                const hzChars = this.wordData.hz[i];
                const pys = this.wordData.pys[i];
                if (pys === null) continue;
                const tr = this.wordData.tr[i];
                for (let j = 0; j < pys.length; j++) {
                    const py = pys[j];
                    const hz = hzChars[j];
                    const key = getKnowledgeKey('py', hz, [py], null);
                    const knowledgeState = getKnowledgeState(k, key);
                    const lvlKnowledgeState = getKnowledgeState(this.lvlKnowledge, key);
                    hasUnknown = hasUnknown || ([KnowledgeUnknown, undefined].includes(knowledgeState) && [KnowledgeUnknown, undefined].includes(lvlKnowledgeState));
                    hasLearning = hasLearning || (knowledgeState == KnowledgeLearning || lvlKnowledgeState == KnowledgeLearning);
                }
                const pyKey = this.knowledgeKey('py', i);
                if (hasLearning) {
                    console.log('COMPOUNDS: Marking pinyin', hzChars, pys, 'as learning');
                    applyKnowledge(d, k, 'py', hzChars, pys, tr, this.wordData.translation, KnowledgeLearning);
                }
                else if (! hasUnknown) {
                    console.log('COMPOUNDS: Marking pinyin', hzChars, pys, 'as known');
                    applyKnowledge(d, k, 'py', hzChars, pys, tr, this.wordData.translation, KnowledgeKnown);
                }
            }
        },
    }
};
</script>

<style>
.peekall {
    width: 1.5em;
    margin-right: 3em;
}

.captioncontent {
    display: inline-block;
    padding-left: 0.25em !important;
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
    font-family: sans-serif;
}

.toprow td:not(:first-child) {
    font-size: 1em;
}

.centerrow td:not(:first-child) {
    font-size: 1.25em;
    line-height: 1.25em;
}

.centerrow {
    vertical-align: bottom;
}

.bottomrow td:not(:first-child) {
    font-size: 0.8em;
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

.captioncard:not(.nonhanzi) {
    cursor: pointer;
}

.captioncard:not(.peeking):not(.nonhanzi):hover {
    background-color: gray;
}

.captioncard.peeking:not(.nonhanzi):hover {
    background-color: gray;
}

.captioncard:not(.peeking):not(.nonhanzi):active {
    background-color: lightgray;
}

.captioncard.peeking {
    padding-left: 2px;
    padding-right: 2px;
}

.centerrow .captioncardhidden {
    border: 1px dashed white;
}

.captioncard.learning .cardcontent {
    color: darkorange;
}

.captioncard.known .cardcontent {
    color: #32de84;
}

.peekall .cardcontent {
    font-size: 0.5em;
    color: lightgray;
    position: absolute;
    line-height: 0;
    left: 0;
    top: 50%;
    width: 100%;
    margin-top: 0em;
}

.peekall:hover .cardcontent {
    visibility: hidden;
}

.iconcard {
    position: absolute;
    line-height: 0;
    height: 20px;
    visibility: hidden;
    z-index: 999;
}

.iconcard.peek {
    left: 0;
    top: 50%;
    width: 100%;
    margin-top: -10px;
}

.iconcard.learn {
    top: -10px;
    right: -7px;
    width: 20px;
}

.iconcard.learn svg {
    background: darkorange;
}

.iconcard.know {
    top: -10px;
    right: -7px;
    width: 20px;
}

.iconcard.know svg {
    background: limegreen;
}

.iconcard.remove {
    top: -10px;
    right: -7px;
    width: 20px;
}

.iconcard.remove svg {
    background: lightgray;
}

.iconcard > svg {
    border-radius: 3px;
    padding: 2px;
}

.captioncard:hover:not(.nonhanzi) .iconcard {
    cursor: pointer;
    visibility: visible;
}

.fulltranslation {
    margin-left: 2em;
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
