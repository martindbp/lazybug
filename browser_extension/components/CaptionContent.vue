<template>
    <div ref="captioncontent" :class="{captioncontent: true, fadeout: fadeOut}">
        <table class="contenttable" ref="wordcontent">
            <tr class="toprow">
                <td title="Peek pinyin row" :class="getClasses('py', null)" @click="clickPeekRow('py')">
                    <span v-if="isPeek('py')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('py')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">PY</span>
                </td>
                <td
                    :class="getClasses('py', i)"
                    @click.stop.prevent="click('py', i)"
                    v-for="(py, i) in wordData.py"
                    :key="i"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: finalShowStates.py[i] ? 1 : 0}"
                    >
                        {{ finalShowStates.py[i] ? py : '-' }}
                    </span>
                    <q-badge :color="wordStats[i] === 1 ? 'red' : 'green'" floating>{{ wordStats[i] }}</q-badge>
                    <ContentContextMenu
                        v-if="showContextMenu.py[i]"
                        type="py"
                        :idx="i"
                        :hide="showStates.py[i]"
                        :pin="purePeekStates.py[i] && knownStates.py[i]"
                        :learn="showStates.py[i] || (purePeekStates.py[i] && knownStates.py[i])"
                        :unlearn="purePeekStates.py[i] && learningStates.py[i]"
                        :dict="true"
                        :click="clickContextMenu"
                    />
                </td>
            </tr>
            <tr class="centerrow">
                <td title="Peek hanzi row" :class="getClasses('hz', null)" @click="clickPeekRow('hz')">
                    <span v-if="isPeek('hz')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('hz')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">HZ</span>
                </td>
                <td
                    :class="getClasses('hz', i)"
                    @click.stop.prevent="click('hz', i)"
                    v-for="(hz, i) in wordData.hz"
                    :key="i"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: finalShowStates.hz[i] ? 1 : 0}"
                    >
                        {{ sm2tr(hz) }}
                    </span>
                    <q-badge :color="wordStats[i] === 1 ? 'red' : 'green'" floating>{{ wordStats[i] }}</q-badge>
                    <ContentContextMenu
                        v-if="showContextMenu.hz[i]"
                        type="hz"
                        :idx="i"
                        :hide="showStates.hz[i]"
                        :pin="purePeekStates.hz[i] && knownStates.hz[i]"
                        :learn="showStates.hz[i] || (purePeekStates.hz[i] && knownStates.hz[i])"
                        :unlearn="purePeekStates.hz[i] && learningStates.hz[i]"
                        :dict="true"
                        :click="clickContextMenu"
                    />
                </td>
            </tr>
            <tr class="bottomrow">
                <td title="Peek word translations" :class="getClasses('tr', null)" @click="clickPeekRow('tr')">
                    <span v-if="isPeek('tr')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('tr')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">TR</span>
                </td>
                <td
                    :class="getClasses('tr', i)"
                    @click.stop.prevent="click('tr', i)"
                    v-for="(tr, i) in wordData.tr"
                    :key="i"
                >
                    <span
                        class="cardcontent"
                        :title="finalShowStates.tr[i] && tr !== null && tr.length > truncateTrLengths[i] ? tr : null"
                        :style="{opacity: finalShowStates.tr[i] ? 1 : 0}"
                    >
                        {{ tr !== null && finalShowStates.tr[i] ? (tr.substring(0, truncateTrLengths[i]) + (tr.length > truncateTrLengths[i] ? '...' : '')) : '-' }}
                    </span>
                    <q-badge :color="wordStats[i] === 1 ? 'red' : 'green'" floating>{{ wordStats[i] }}</q-badge>
                    <ContentContextMenu
                        v-if="showContextMenu.tr[i]"
                        type="tr"
                        :idx="i"
                        :hide="showStates.tr[i]"
                        :pin="purePeekStates.tr[i] && knownStates.tr[i]"
                        :learn="showStates.tr[i] || (purePeekStates.tr[i] && knownStates.tr[i])"
                        :unlearn="purePeekStates.tr[i] && learningStates.tr[i]"
                        :dict="true"
                        :click="clickContextMenu"
                    />
                </td>
            </tr>
        </table>
        <br/>
        <table class="contenttable" style="margin-top: -15px">
            <tr>
                <td title="Peek sentence translation" :class="getClasses('translation', null)" @click="clickPeekRow('translation')">
                    <span v-if="isPeek('translation')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('translation')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">EN</span>
                </td>
                <td
                    ref="fulltranslation"
                    @click.stop.prevent="click('translation')"
                    :class="{
                        captioncard: true,
                        peeking: purePeekStates.translation,
                        learning: learningStates.translation,
                        fulltranslation: true,
                        placeholder: !finalShowStates.translation,
                        showborder: data !== null,
                    }"
                >
                    <span class="cardcontent" :style="{ opacity: finalShowStates['translation'] ? 1 : 0 }"> {{ translation }}</span>
                    <span style="position: absolute; left: 50%" v-if="!finalShowStates['translation']" v-html="eyecon"></span>
                    <ContentContextMenu
                        v-if="showContextMenu.translation"
                        type="translation"
                        :learn="! learningStates.translation"
                        :unlearn="learningStates.translation"
                        :pin="false"
                        :hide="false"
                        :dict="false"
                        :click="clickContextMenu"
                    />
                </td>
            </tr>
        </table>
    </div>
</template>
<script>
import SvgButton from './SvgButton.vue'
import ContentContextMenu from './ContentContextMenu.vue'

export default {
    mixins: [mixin],
    components: {
        SvgButton,
        ContentContextMenu,
    },
    props: {
        data: { default: null },
        currTime: { default: null },
        fadeOut: { default: false },
    },
    data: function () { return {
        eyecon: getIconSvg("eye", 18),
        pinIcon: getIconSvg("pin", 18),
        unpinIcon: getIconSvg("unpin", 18),
        bookIcon: getIconSvg("study", 18),
        checkIcon: getIconSvg("check", 18),
        undoIcon: getIconSvg("undo", 18),
        showContextMenu: {hz: [], tr: [], py: [], translation: false},
    }},
    computed: {
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
                const trunateLength = Math.max(15, Math.ceil(Math.max(this.wordData.py[i].length, this.wordData.hz[i].length) * 2))  // add 100% to longest
                outLengths.push(trunateLength);
            }
            return outLengths;
        },
        translation: function() {
            if (this.data == null) return '';
            const useTranslationIdx = Math.min(this.$store.state.options.displayTranslation, this.data.translations.length-1);
            return this.data.translations[useTranslationIdx];
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

            wordData.translation = this.translation;

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
                        getKnowledgeState(this.$store.state.knowledge, this.knowledgeKey(type, i), KnowledgeKnown)
                    );
                    states[type].push(isUnknown);
                }
            }
            return states;
        },
        finalShowStates: function() {
            // Show states that include the peek states
            const states = {'py': [], 'hz': [], 'tr': [], 'translation': this.showStates['translation'] || this.purePeekStates['translation']};
            for (let i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = this.showStates[type][i] || this.purePeekStates[type][i];
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
    updated: function() {
        // New text may have changed the size of the caption, so need to update width of full translation table
        const self = this;
        this.$nextTick(function () {
            if (! [null, undefined].includes(self.$refs.captioncontent)) {
                const topLeftWidth = self.$refs.wordcontent.children[0].children[0].clientWidth;
                const totalRowWidth = self.$refs.wordcontent.clientWidth;
                self.$refs.fulltranslation.style.minWidth = (totalRowWidth - topLeftWidth) + 'px';
            }
        });
    },
    mounted: function() {
        const self = this;
        document.addEventListener('click', function(event) {
            self.resetShowContextMenu(self.wordData);
        });
    },
    watch: {
        data: {
            immediate: true,
            handler: function(newData, oldData) {
                if (newData !== oldData) {
                    this.applyKnownLvls();
                    this.applyKnownPinyinComponents();
                    this.applyKnownCompoundWordsNotInDict();
                    this.$store.commit('resetPeekStates', this.wordData.hz.length);
                    for (const type of ['hz', 'tr', 'py', 'translation']) {
                        if (this.$store.state.options.pin[type] === true) {
                            this.$store.commit('setPeekState', {'type': type});
                        }
                    }
                }
            },
        },
        wordData: function(newData, oldData) {
            this.resetShowContextMenu(newData);
        }
    },
    methods: {
        resetShowContextMenu: function(newData) {
            const show = {
                translation: false,
                hz: [],
                tr: [],
                py: []
            }
            for (let i = 0; i < newData.hz.length; i++) {
                show.hz.push(false);
                show.tr.push(false);
                show.py.push(false);
            }
            this.showContextMenu = show;
        },
        isPeek: function(type) {
            return (
                !this.$store.state.peekStates.rows[type] &&
                !this.$store.state.options.pin[type]
            );
        },
        getClasses: function(type, i) {
            const cl = {
                captioncard: true,
                peeking: i !== null && this.purePeekStates[type][i],
                captioncardhidden: i !== null && ! this.finalShowStates[type][i],
                nonhanzi: i !== null && this.wordData.pys[i] === null,
                learning: i !== null && this.learningStates[type][i],
                known: i !== null && this.knownStates[type][i],
                peekrow: i === null,
                pinned: this.$store.state.options.pin[type],
            };
            return cl;
        },
        getStates: function(compareTo) {
            const translationState = getKnowledgeState(this.$store.state.knowledge, this.knowledgeKey('translation'), compareTo)
            const states = {'py': [], 'hz': [], 'tr': [], 'translation': translationState === compareTo};
            for (let i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    const state = getKnowledgeState(this.$store.state.knowledge, this.knowledgeKey(type, i), compareTo);
                    states[type].push(state === compareTo);
                }
            }
            return states;
        },
        knowledgeKey: function(type, i = null) {
            return getKnowledgeKey(
                type,
                i === null ? null : this.wordData.hz[i],
                i === null ? null : this.wordData.pys[i],
                i === null ? null : this.wordData.tr[i],
                this.wordData.translation
            );
        },
        clickContextMenu(action, type, i) {
            const d = this.$store.state.DICT;
            const k = this.$store.state.knowledge;

            const pys = i === null ? null : this.wordData.pys[i];
            const hz = i === null ? null : this.wordData.hz[i];
            const tr = i === null ? null : this.wordData.tr[i];

            let setState = null;
            let stateType = null;
            if (action === 'hide') {
                stateType = KnowledgeKnown;
                setState = KnowledgeKnown;
            }
            else if (action === 'learn') {
                stateType = KnowledgeLearning;
                setState = KnowledgeLearning;
            }
            else if (action === 'pin') {
                stateType = KnowledgeKnown;
                setState = KnowledgeUnknown;
            }
            else if (action === 'unlearn') {
                stateType = KnowledgeLearning;
                setState = KnowledgeUnknown;
            }

            if (setState !== null) {
                applyKnowledge(d, k, type, hz, pys, tr, this.wordData.translation, stateType, setState, true);
                this.appendSessionLog([getEvent(action, type), i]);
            }
            else if (action === 'dict') {
                let [startIdx, endIdx, ...rest] = this.data.alignments[i];
                this.$store.commit('setShowDictionary', {val: true, range: [startIdx, endIdx]});
            }
            this.resetShowContextMenu(this.wordData);
        },
        click: function(type, i = null) {
            if (type === 'translation' && this.showStates[type] === false) {
                if (this.finalShowStates[type] === true) {
                    const lastVal = this.showContextMenu[type];
                    this.resetShowContextMenu(this.wordData);
                    this.showContextMenu[type] = ! lastVal;
                }
                else {
                    this.$store.commit('setPeekState', {'type': type, 'i': i});
                    this.appendSessionLog([getEvent('peek', 'translation')]);
                }
                return;
            }

            if (this.wordData.pys[i] === null) return;

            if (this.showStates[type][i] === false && ! this.purePeekStates[type][i]) {
                this.$store.commit('setPeekState', {'type': type, 'i': i});
                this.appendSessionLog([getEvent('peek', 'tr'), i]);
            }
            else {
                const lastVal = this.showContextMenu[type][i];
                this.resetShowContextMenu(this.wordData);
                this.showContextMenu[type][i] = ! lastVal;
            }
        },
        clickPeekRow: function(type) {
            if (this.$store.state.options.pin[type] === true) {
                this.$store.commit('setDeepOption', {key: 'pin', key2: type, value: false});
                this.appendSessionLog([getEvent('pin_row', type), false]);
            }
            else if (this.$store.state.peekStates.rows[type] === true) {
                this.$store.commit('setDeepOption', {key: 'pin', key2: type, value: true});
                this.appendSessionLog([getEvent('pin_row', type), true]);
            }
            else {
                this.$store.commit('setPeekState', {'type': type});
                this.appendSessionLog([getEvent('peek_row', type)]);
            }
        },
        applyKnownLvls: function() {
            const d = this.$store.state.DICT;
            const k = this.$store.state.knowledge;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.pys[i] == null ? '' : this.wordData.hz[i];
                if (hz.length === 0) continue;
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                for (var type of ['hz', 'py', 'tr']) {
                    const key = this.knowledgeKey(type, i);
                    if (
                        [KnowledgeUnknown, undefined].includes(getKnowledgeState(k, key, KnowledgeKnown)) &&
                        getKnowledgeState(this.lvlKnowledge, key, KnowledgeKnown) == KnowledgeKnown
                    ) {
                        console.log('LVLS: Marking', type, hz, pys, tr, 'as known');
                        applyKnowledge(d, k, type, hz, pys, tr, this.wordData.translation, KnowledgeKnown, KnowledgeKnown, false, true);
                        this.appendSessionLog([getEvent('hide_auto', type), i]);
                    }
                }
            }
        },
        applyKnownPinyinComponents: function() {
            // If user knows ni3hao3, he should know ni3 and hao3 separately, but not other way around.

            const d = this.$store.state.DICT;
            const k = this.$store.state.knowledge;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.hz[i];
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                if (d[hz] !== undefined || pys === null || isName(tr)) continue;

                let words = [];
                for (let w = 5; w >= 1; w--) {
                    for (let startIdx = 0; startIdx < hz.length-w+1; startIdx++) {
                        const endIdx = startIdx + w;
                        const hzSub = hz.substring(startIdx, endIdx);
                        const pysSub = pys.slice(startIdx, endIdx);
                        if (hzSub === hz) continue;
                        if (d[hzSub] === undefined) continue;

                        console.log('applyKnownPinyinComponents: ', 'py', hzSub, pysSub);
                        applyKnowledge(d, k, 'py', hzSub, pysSub, null, this.wordData.translation, KnowledgeKnown, KnowledgeKnown, false, true);
                    }
                }
            }
        },
        applyKnownCompoundWordsNotInDict: function() {
            // If word is not in dict, but we know all the sub-words, then we say we know the compound (for hz and tr)
            // The reasoning is, if it's not in the dictionary, it's more likely to be a compound of regular words that
            // have a similar meaning to the parts. If it had a very different meaning, then it should be in the dictionary.
            const d = this.$store.state.DICT;
            const k = this.$store.state.knowledge;
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

                let knowAll = {hz: true, tr: true};
                for (const [wordHz, wordPys] of words) {
                    for (const type of ['hz', 'tr']) {
                        const key = getKnowledgeKey(type, wordHz, wordPys, null, null);
                        knowAll[type] = knowAll[type] && (
                            getKnowledgeState(this.lvlKnowledge, key, KnowledgeKnown) === KnowledgeKnown ||
                            getKnowledgeState(this.$store.state.knowledge, key, KnowledgeKnown) === KnowledgeKnown
                        );
                    }
                }

                for (const type of ['hz', 'tr']) {
                    if (getKnowledgeState(k, this.knowledgeKey(type, i), KnowledgeKnown) === KnowledgeKnown) {
                        continue;
                    }

                    if (knowAll[type]) {
                        console.log('applyKnownCompoundWordsNotInDict', type, hz, pys);
                        applyKnowledge(d, k, type, hz, pys, null, null, KnowledgeKnown, KnowledgeKnown, false, true);
                        this.appendSessionLog([getEvent('hide_auto', type), i]);
                    }
                }
            }
        },
    }
};
</script>

<style>
.peekrow {
    width: 1.5em;
    margin-right: 3em;
}

.captioncontent {
    font-family: 'Heiti SC';
    width: 100%;
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

.contenttable {
    display: inline-block;
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
    user-select: none;
    white-space: nowrap;
    border: 1px solid transparent;
    border-radius: 5px;
}

.captioncard:not(.nonhanzi) {
    cursor: pointer;
}

.captioncard:not(.nonhanzi):hover {
    background-color: gray;
}

.captioncard:not(.nonhanzi):active {
    background-color: lightgray;
}

.captioncard.peeking:not(.fulltranslation) {
    padding-left: 2px;
    padding-right: 2px;
}

.centerrow .captioncardhidden {
    border: 1px dashed white;
}

.captioncardhidden.learning {
    border: 1px dashed darkorange;
}

.captioncard.learning .cardcontent {
    color: darkorange;
}

.captioncard.known .cardcontent {
    color: #32de84;
}

.peekrow .cardcontent {
    font-size: 0.5em;
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
}

.pinned.peekrow .iconcard {
    visibility: visible;
}

.pinned.peekrow .cardcontent {
    visibility: hidden;
}

.pinned.peekrow svg {
    background-color: #606060;
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

.captioncardhidden .q-badge {
    display: none !important;
}

.captioncard:not(:hover) .q-badge {
    display: none !important;
}

.captioncard .q-badge {
    margin-top: -5px;
    margin-right: -5px;
}
</style>
