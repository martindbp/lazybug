<template>
    <div ref="captioncontent" :class="{captioncontent: true, fadeout: fadeOut}">
        <table class="contenttable" ref="wordcontent">
            <tr class="toprow">
                <td v-if="data !== null" title="Peek pinyin row" :class="getClasses('py', null, true)" @click="clickPeekRow('py')" :style="tdStyle" >
                    <span v-if="! $store.state.options.pin.py" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="$store.state.options.pin.py" class="iconcard peek cardcontent" v-html="pinIcon" style="visibility: visible !important"></span>
                    <span v-else class="cardcontent">PY</span>

                    <ContentContextMenu
                        type="py"
                        :pin="showPinRow('py')"
                        :unpin="!showPinRow('py')"
                        :copy="true"
                        :options="true"
                        :click="clickRowContextMenu"
                    />
                </td>
                <td
                    :class="getClasses('py', i)"
                    @click.stop.prevent="click('py', i)"
                    v-for="(py, i) in wordData.py"
                    :key="i"
                    :style="tdStyle"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: hiddenAndNotPeeking.py[i] ? 0 : 1}"
                    >
                        {{ hiddenAndNotPeeking.py[i] ? '-' : py }}
                    </span>
                    <span v-if="hiddenAndNotPeeking.py[i]" class="iconcard peek" v-html="eyecon"></span>
                </td>
            </tr>
            <tr class="centerrow">
                <td v-if="data !== null" title="Peek hanzi row" :class="getClasses('hz', null, true)" @click="clickPeekRow('hz')" :style="tdStyle">
                    <span v-if="! $store.state.options.pin.hz" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="$store.state.options.pin.hz" class="iconcard peek cardcontent" v-html="pinIcon" style="visibility: visible !important"></span>
                    <span v-else class="cardcontent">HZ</span>

                    <ContentContextMenu
                        type="hz"
                        :pin="showPinRow('hz')"
                        :unpin="!showPinRow('hz')"
                        :copy="true"
                        :options="true"
                        :click="clickRowContextMenu"
                    />
                </td>
                <td
                    :class="getClasses('hz', i)"
                    @click.stop.prevent="click('hz', i)"
                    v-for="(hz, i) in wordData.hz"
                    :key="i"
                    :style="tdStyle"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: hiddenAndNotPeeking.hz[i] ? 0 : 1}"
                    >
                        {{ sm2tr(hz) }}
                        <q-badge v-if="starredStates.words[i]" class="starbadge" color="transparent" rounded floating v-html="smallStarIcon"></q-badge>
                    </span>
                    <q-badge class="statsbadge" :color="wordStats[i] === 1 ? 'red' : 'green'" floating>{{ wordStats[i] }}</q-badge>
                    <span v-if="hiddenAndNotPeeking.hz[i]" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="purePeekStates.hz[i]" class="iconcard peek" v-html="pinIcon"></span>
                    <span v-if="!hiddenStates.hz[i]" class="iconcard peek" v-html="hideIcon"></span>
                    <ContentContextMenu
                        type="word"
                        :idx="i"
                        :star="!hiddenAndNotPeeking.hz[i] && ! starredStates.words[i]"
                        :unstar="starredStates.words[i]"
                        :dict="true"
                        :click="clickContextMenu"
                        :copy="true"
                    />
                </td>
            </tr>
            <tr class="bottomrow">
                <td v-if="data !== null" title="Peek word translations" :class="getClasses('tr', null, true)" @click="clickPeekRow('tr')" :style="tdStyle">
                    <span v-if="! $store.state.options.pin.tr" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="$store.state.options.pin.tr" class="iconcard peek cardcontent" v-html="pinIcon" style="visibility: visible !important"></span>
                    <span v-else class="cardcontent">TR</span>
                    <ContentContextMenu
                        type="tr"
                        :pin="showPinRow('tr')"
                        :unpin="!showPinRow('tr')"
                        :options="true"
                        :click="clickRowContextMenu"
                    />
                </td>
                <td
                    :class="getClasses('tr', i)"
                    @click.stop.prevent="click('tr', i)"
                    v-for="(tr, i) in wordData.tr"
                    :key="i"
                    :style="tdStyle"
                >
                    <span
                        class="cardcontent"
                        :title="!hiddenAndNotPeeking.tr[i] && tr !== null && tr.length > truncateTrLengths[i] ? tr : null"
                        :style="{opacity: hiddenAndNotPeeking.tr[i] ? 0 : 1}"
                    >
                        {{ tr !== null && !hiddenAndNotPeeking.tr[i] ? (tr.substring(0, truncateTrLengths[i]) + (tr.length > truncateTrLengths[i] ? '...' : '')) : '-' }}
                    </span>
                    <span v-if="hiddenAndNotPeeking.tr[i]" class="iconcard peek" v-html="eyecon"></span>
                </td>
            </tr>
        </table>
        <br/>
        <table class="contenttable" :style="{ fontSize: $store.state.captionFontSize+'px !important', marginTop: '0.2em' }" v-if="data !== null">
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
                        :switch="data.translations.length > 1"
                        :switchlabel="translationIdx === 0 ? 'Switch to Machine translations' : 'Switch to Human translations'"
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
        currentCaptionIdx: { default: null },
        videoAPI: { default: null },
    },
    data: function () { return {
        eyecon: getIconSvg("eye", 18),
        pinIcon: getIconSvg("pin", 18),
        hideIcon: getIconSvg("hide", 18),
        unpinIcon: getIconSvg("unpin", 18),
        smallStarIcon: getIconSvg("star", 10, 'darkorange'),
        autoPeeked: null,
    }},
    computed: {
        tdStyle: function() {
            return {
                fontSize: this.$store.state.captionFontSize+'px !important',
                padding: 0,
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
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = this.hiddenStates[type][i] && ! this.purePeekStates[type][i];
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
    },
    updated: function() {
        // New text may have changed the size of the caption, so need to update width of full translation table
        const self = this;
        this.$nextTick(function () {
            if (! [null, undefined].includes(self.$refs.captioncontent)) {
                const peekCells = self.$refs.wordcontent.children[0].children;
                if (peekCells.length > 0) {
                    const topLeftWidth = peekCells[0].clientWidth;
                    const totalRowWidth = self.$refs.wordcontent.clientWidth;
                    self.$refs.fulltranslation.style.minWidth = (totalRowWidth - topLeftWidth) + 'px';
                }
            }
        });
    },
    watch: {
        data: {
            immediate: true,
            handler: function(newData, oldData) {
                if (newData !== oldData) {
                    this.$store.commit('resetPeekStates', this.wordData.hz.length);
                    this.applyLvlStates();
                    this.applyComponents();
                    this.applyCompoundWordsNotInDict();
                    this.applySimpleCompounds();
                }
            },
        },
    },
    methods: {
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
                hiddenstate: i !== null && this.hiddenStates[type][i] && ! this.starredStates.words[i],
                peekrow: i === null,
                autopeek: i !== null && this.$store.state.autoPeekStates[type][i],
                pinned: this.$store.state.options.pin[type],
                nonhanzirow: type !== 'hz' && ! isPeekRow,
            };
            return cl;
        },
        stateKey: function(type, i = null) {
            return wordDataStateKey(this.wordData, type, i);
        },
        clickPeekRow: function(type) {
            this.$store.commit('setPeekState', {'type': type});
            this.appendSessionLog([getEvent('peek_row', type)]);
        },
        clickRowContextMenu(action, type) {
            this.videoAPI.pause();

            if (action === 'copy') {
                if (type === 'translation') {
                    updateClipboard(this.wordData[type], this.$q, 'Copied to clipboard');
                }
                else if (type === 'py') {
                    updateClipboard(this.wordData.py.join(' '), this.$q, 'Copied to clipboard');
                }
                else if (type === 'hz') {
                    updateClipboard(this.wordData.text, this.$q, 'Copied to clipboard');
                }
                return;
            }
            else if (action === 'options') {
                this.$store.commit('setOptionsHighlightSection', `knowledge-${type}-lvl`);
                this.$store.commit('setShowOptions', true);
                return;
            }

            this.$store.commit('setDeepOption', {key: 'pin', key2: type, value: action === 'pin'});
            this.appendSessionLog([getEvent('pin_row', type), action === 'pin']);
            if (action === 'pin') {
                this.$store.commit('setPeekState', {'type': type});
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

                this.applyState(type, i, StateStarred, StateStarred);

                const self = this;
                this.$q.notify({
                    type: 'positive',
                    message: `"${content}" starred`,
                    actions: [
                        { label: 'Open starred', color: 'white', handler: function() { self.$store.commit('setPage', 'star'); } }
                    ]
                });
            }
            else if (action === 'unstar') {
                this.applyState(type, i, StateStarred, StateNone);
            }

            if (action === 'dict') {
                let [startIdx, endIdx, ...rest] = this.data.alignments[i];
                this.$store.commit('setShowDictionary', {val: true, range: [startIdx, endIdx]});
            }
            else if (action === 'copy') {
                if (type === 'translation') {
                    updateClipboard(this.wordData[type], this.$q, 'Copied to clipboard');
                }
                else {
                    const text = `${this.wordData.hz[i]}-${this.wordData.py[i]}-${this.wordData.tr[i]}`;
                    updateClipboard(text, this.$q, 'Copied to clipboard');
                }
            }
            else if (action === 'switch') {
                this.$store.commit('switchTranslation');
            }
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
            const dt = Date.now() - this.$store.state.sessionTime;
            let captionIdx = this.currentCaptionIdx;
            if (Array.isArray(captionIdx)) {
                captionIdx = captionIdx[0];
            }
            return {
                data: this.data,
                translationIdx: this.translationIdx,
                hidden: this.hiddenStates,
                dt: dt,
                captionIdx: captionIdx,
            };
        },
        click: function(type, i = null) {
            this.videoAPI.pause();
            if (type === 'translation') {
                if (this.hiddenAndNotPeeking[type] === true) {
                    this.$store.commit('setPeekState', {'type': type, 'i': i});
                    this.applyState(type, i, StateHidden, StateNone);
                }
                return;
            }

            if (this.wordData.pys[i] === null) return;

            if (this.hiddenStates[type][i] === true) {
                if (! this.purePeekStates[type][i]) {
                    this.$store.commit('setPeekState', {'type': type, 'i': i});
                    this.appendSessionLog([getEvent('peek', 'tr'), i]);
                }
                else if (type === 'hz') {
                    this.applyState('word', i, StateHidden, StateNone); // Pin it
                }
            }
            else if (type === 'hz') {
                this.applyState('word', i, StateHidden, StateHidden); // Hide it
                // Also peek all three. This makes it more intuitive that if you click again you pin it back
                for (const t of ['py', 'hz', 'tr']) {
                    this.$store.commit('setPeekState', {'type': t, 'i': i});
                }
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
            if (this.$store.state.options.peekAfterAutoHide) {
                for (const type of ['py', 'hz', 'tr']) {
                    this.$store.commit('setPeekState', {'type': type, 'i': i});
                    this.$store.commit('setPeekState', {'type': type, 'i': i, 'auto': true});
                }
                this.appendSessionLog([getEvent('peek', 'word'), i]);
            }
        },
        applyLvlStates: function() {
            const d = this.$store.state.DICT;
            const k = this.$store.state.states;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.pys[i] == null ? '' : this.wordData.hz[i];
                if (hz.length === 0) continue;
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];
                const key = this.stateKey('word', i);
                if (
                    getState(k, key, StateHidden, StateNone) === StateNone &&
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

                // Peek the ones that are pinned
                for (const type of ['py', 'hz', 'tr']) {
                    if (
                        getState(k, key, StateHidden, StateHidden) && // the word is hidden
                        this.$store.state.options.pin[type] && // pin for this type is on
                        getState(this.pinLevelStates[type], key, StateHidden, StateNone) !== StateHidden // this word+type should be pinned
                    ) {
                        console.log('Auto pinning', type, key);
                        this.$store.commit('setPeekState', {'type': type, 'i': i});
                        this.$store.commit('setPeekState', {'type': type, 'i': i, 'auto': true});
                        this.appendSessionLog([getEvent('peek', type), i]);
                    }
                }
            }

            // Peek full translation
            if (this.$store.state.options.pin.translation) {
                this.$store.commit('setPeekState', {'type': 'translation'});
                this.$store.commit('setPeekState', {'type': 'translation', 'auto': true});
                this.appendSessionLog([getEvent('peek', 'translation')]);
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
                    if (getState(k, this.stateKey('word', i), StateHidden, StateNone) === StateNone) {
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
    color: white;
    font-size: 24px;
    display: inline-block;
    text-align: center;
    table-layout: fixed;
    border-spacing: 0.3em;
    font-family: sans-serif;
}

.contenttable tr {
    line-height: 1.5em;
}

.toprow td:not(:first-child) span {
    font-size: 1em;
}

.centerrow td:not(:first-child) {
    line-height: 1.25em;
}

.centerrow td:not(:first-child) span {
    font-size: 1.25em;
}

.centerrow {
    vertical-align: bottom;
}

.bottomrow td:not(:first-child) span {
    font-size: 0.8em;
}

.captioncard {
    position: relative;
    user-select: none;
    white-space: nowrap;
    border: 1px solid transparent;
    border-radius: 5px;
}

.captioncard:not(.nonhanzi):not(.nonhanzirow:not(.captioncardhidden)) {
    cursor: pointer;
}

.captioncard:not(.nonhanzi):not(.nonhanzirow:not(.captioncardhidden)):hover {
    background-color: gray;
}

.captioncard:not(.nonhanzi):not(.nonhanzirow:not(.captioncardhidden)):active {
    background-color: lightgray;
}

.captioncard.peeking:not(.fulltranslation) {
    padding-left: 2px;
    padding-right: 2px;
}

.centerrow .captioncardhidden {
    border: 1px dashed white;
    border-radius: 3px;
}

.centerrow .captioncardhidden.starred  {
    border: 1px dashed darkorange !important;
}

.cardcontent {
    position: relative;
}

.captioncard.peeking:not(.fulltranslation) .cardcontent {
    color: rgb(180, 180, 180);
}

.captioncard.autopeek.hiddenstate .cardcontent {
    color: rgb(100, 100, 100) !important;
}

.captioncard.pinned.hiddenstate .cardcontent {
    color: rgb(180, 180, 180) !important;
}

.captioncard:hover:not(.nonhanzi):not(.fulltranslation):not(.nonhanzirow:not(.captioncardhidden)) .cardcontent {
    color: rgb(100, 100, 100) !important;
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

.fulltranslation > .cardcontent {
    padding-left: 0.3em;
    padding-right: 0.3em;
}

.captioncardhidden .statsbadge {
    display: none !important;
}

.captioncard:not(:hover) .statsbadge {
    display: none !important;
}

.nonhanzi .statsbadge {
    display: none !important;
}

.captioncard .statsbadge {
    margin-top: -5px;
    margin-right: -5px;
}

.captioncard:hover:not(.fulltranslation):not(.captioncardhidden) .starbadge {
    display: none !important;
}

.captioncardhidden .starbadge {
    display: none !important;
}

.captioncard .starbadge {
    margin-top: -5px;
    margin-right: -10px;
}

</style>
