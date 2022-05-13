<template>
    <div ref="captioncontent" :class="{captioncontent: true, fadeout: fadeOut}">
        <table class="contenttable" ref="wordcontent">
            <tr class="toprow">
                <td v-if="data !== null" title="Peek pinyin row" :class="getClasses('py', null)" @click="clickPeekRow('py')">
                    <span v-if="isPeek('py')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('py')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">PY</span>
                </td>
                <td
                    :class="getClasses('py', i)"
                    @click.stop.prevent="click('py', i)"
                    v-for="(py, i) in wordData.py"
                    :key="i"
                    @mouseleave="mouseleave($event, 'py', i)"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: hiddenAndNotPeeking.py[i] ? 0 : 1}"
                    >
                        {{ hiddenAndNotPeeking.py[i] ? '-' : py }}
                    </span>
                    <q-badge class="statsbadge" :color="wordStats[i] === 1 ? 'red' : 'green'" floating>{{ wordStats[i] }}</q-badge>
                    <ContentContextMenu
                        v-if="showContextMenu.py[i]"
                        type="py"
                        :idx="i"
                        :hide="!hiddenStates.py[i]"
                        :pin="purePeekStates.py[i] && hiddenStates.py[i]"
                        :star="!hiddenAndNotPeeking.py[i] && ! starredStates.words[i]"
                        :unstar="starredStates.words[i]"
                        :dict="true"
                        :click="clickContextMenu"
                        :copy="true"
                    />
                </td>
            </tr>
            <tr class="centerrow">
                <td v-if="data !== null" title="Peek hanzi row" :class="getClasses('hz', null)" @click="clickPeekRow('hz')">
                    <span v-if="isPeek('hz')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('hz')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">HZ</span>
                </td>
                <td
                    :class="getClasses('hz', i)"
                    @click.stop.prevent="click('hz', i)"
                    v-for="(hz, i) in wordData.hz"
                    :key="i"
                    @mouseleave="mouseleave($event, 'hz', i)"
                >
                    <span
                        class="cardcontent"
                        :style="{opacity: hiddenAndNotPeeking.hz[i] ? 0 : 1}"
                    >
                        {{ sm2tr(hz) }}
                        <q-badge v-if="starredStates.words[i]" class="starbadge" color="transparent" rounded floating v-html="smallStarIcon"></q-badge>
                    </span>
                    <q-badge class="statsbadge" :color="wordStats[i] === 1 ? 'red' : 'green'" floating>{{ wordStats[i] }}</q-badge>
                    <ContentContextMenu
                        v-if="showContextMenu.hz[i]"
                        type="hz"
                        :idx="i"
                        :hide="!hiddenStates.hz[i]"
                        :pin="purePeekStates.hz[i] && hiddenStates.hz[i]"
                        :star="!hiddenAndNotPeeking.hz[i] && ! starredStates.words[i]"
                        :unstar="starredStates.words[i]"
                        :dict="true"
                        :click="clickContextMenu"
                        :copy="true"
                    />
                </td>
            </tr>
            <tr class="bottomrow">
                <td v-if="data !== null" title="Peek word translations" :class="getClasses('tr', null)" @click="clickPeekRow('tr')">
                    <span v-if="isPeek('tr')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('tr')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">TR</span>
                </td>
                <td
                    :class="getClasses('tr', i)"
                    @click.stop.prevent="click('tr', i)"
                    v-for="(tr, i) in wordData.tr"
                    :key="i"
                    @mouseleave="mouseleave($event, 'tr', i)"
                >
                    <span
                        class="cardcontent"
                        :title="!hiddenAndNotPeeking.tr[i] && tr !== null && tr.length > truncateTrLengths[i] ? tr : null"
                        :style="{opacity: hiddenAndNotPeeking.tr[i] ? 0 : 1}"
                    >
                        {{ tr !== null && !hiddenAndNotPeeking.tr[i] ? (tr.substring(0, truncateTrLengths[i]) + (tr.length > truncateTrLengths[i] ? '...' : '')) : '-' }}
                    </span>
                    <q-badge class="statsbadge" :color="wordStats[i] === 1 ? 'red' : 'green'" floating>{{ wordStats[i] }}</q-badge>
                    <ContentContextMenu
                        v-if="showContextMenu.tr[i]"
                        type="tr"
                        :idx="i"
                        :hide="!hiddenStates.tr[i]"
                        :pin="purePeekStates.tr[i] && hiddenStates.tr[i]"
                        :star="!hiddenAndNotPeeking.tr[i] && ! starredStates.words[i]"
                        :unstar="starredStates.words[i]"
                        :dict="true"
                        :click="clickContextMenu"
                        :copy="true"
                    />
                </td>
            </tr>
        </table>
        <br/>
        <table class="contenttable" style="margin-top: -15px" v-if="data !== null">
            <tr>
                <td v-if="data !== null" title="Peek sentence translation" :class="getClasses('translation', null)" @click="clickPeekRow('translation')">
                    <span v-if="isPeek('translation')" class="iconcard peek" v-html="eyecon"></span>
                    <span v-if="!isPeek('translation')" class="iconcard peek" v-html="pinIcon"></span>
                    <span class="cardcontent">EN</span>
                </td>
                <td
                    ref="fulltranslation"
                    @click.stop.prevent="click('translation')"
                    @mouseleave="mouseleave($event, 'translation')"
                    :class="{
                        captioncard: true,
                        peeking: purePeekStates.translation,
                        starred: starredStates.translation,
                        fulltranslation: true,
                        placeholder: hiddenAndNotPeeking.translation,
                        showborder: data !== null,
                    }"
                >
                    <span class="cardcontent" :style="{ opacity: hiddenAndNotPeeking['translation'] ? 0 : 1 }">
                        {{ translation }}
                        <q-badge v-if="starredStates.translation" class="starbadge" color="transparent" rounded floating v-html="smallStarIcon"></q-badge>
                    </span>
                    <span style="position: absolute; left: 50%" v-if="hiddenAndNotPeeking['translation']" v-html="eyecon"></span>
                    <ContentContextMenu
                        v-if="showContextMenu.translation"
                        type="translation"
                        :star="! starredStates.translation"
                        :unstar="starredStates.translation"
                        :pin="false"
                        :hide="false"
                        :dict="false"
                        :click="clickContextMenu"
                        :copy="true"
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
    },
    data: function () { return {
        eyecon: getIconSvg("eye", 18),
        pinIcon: getIconSvg("pin", 18),
        unpinIcon: getIconSvg("unpin", 18),
        bookIcon: getIconSvg("study", 18),
        checkIcon: getIconSvg("check", 18),
        undoIcon: getIconSvg("undo", 18),
        smallStarIcon: getIconSvg("star", 10, 'darkorange'),
        showContextMenu: {hz: [], tr: [], py: [], translation: false},
        waitingBeforeClosingMenu: false,
        cancelCloseContextMenu: false,
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
            return getWordData(this.data, this.translationIdx);
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
                    this.applyLvlStates();
                    this.applyPinyinComponents();
                    this.applyCompoundWordsNotInDict();
                    this.applySimpleCompounds();
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
                captioncardhidden: i !== null && this.hiddenAndNotPeeking[type][i],
                nonhanzi: i !== null && this.wordData.pys[i] === null,
                starred: i !== null && this.starredStates.words[i],
                hiddenstate: i !== null && this.hiddenStates[type][i] && ! this.starredStates.words[i],
                peekrow: i === null,
                pinned: this.$store.state.options.pin[type],
            };
            return cl;
        },
        stateKey: function(type, i = null) {
            return wordDataStateKey(this.wordData, type, i);
        },
        clickContextMenu(action, type, i) {
            if (this.waitingBeforeClosingMenu) {
                this.cancelCloseContextMenu = true;
            }
            const d = this.$store.state.DICT;
            const k = this.$store.state.states;

            const pys = i === null ? null : this.wordData.pys[i];
            const hz = i === null ? null : this.wordData.hz[i];
            const tr = i === null ? null : this.wordData.tr[i];

            let setState = null;
            let stateType = null;
            if (action === 'hide') {
                stateType = StateHidden;
                setState = StateHidden;
                // Peek it so that it doesn't become hidden right away
                this.$store.commit('setPeekState', {'type': type, 'i': i});
            }
            else if (action === 'star') {
                stateType = StateStarred;
                setState = StateStarred;
                let content = '';
                if (type === 'translation') content = this.wordData.translation;
                else {
                    content = `${this.wordData.hz[i]}/${this.wordData.py[i]}`;
                    type = 'word';
                }

                this.$q.notify({
                    type: 'positive',
                    message: `"${content}" starred`,
                    actions: [
                        { label: 'Open in Dashboard', color: 'white', handler: openDashboard }
                    ]
                });
            }
            else if (action === 'pin') {
                stateType = StateHidden;
                setState = StateNone;
            }
            else if (action === 'unstar') {
                stateType = StateStarred;
                setState = StateNone;
                type = 'word';
            }

            if (setState !== null) {
                applyState(d, k, type, hz, pys, tr, this.wordData.translation, stateType, setState, true, true);
                const eventData = [getEvent(action, type), i];
                if (setState === StateStarred) {
                    eventData.push(this.getCurrentState());
                }
                this.appendSessionLog(eventData);
            }
            else if (action === 'dict') {
                let [startIdx, endIdx, ...rest] = this.data.alignments[i];
                this.$store.commit('setShowDictionary', {val: true, range: [startIdx, endIdx]});
            }
            else if (action === 'copy') {
                if (type === 'translation') {
                    updateClipboard(this.wordData[type], this.$q, 'Copied to clipboard');
                }
                else {
                    updateClipboard(this.wordData[type][i], this.$q, 'Copied to clipboard');
                }
            }

            if (['dict', 'copy'].includes(action)) {
                this.resetShowContextMenu(this.wordData);
            }
        },
        getCurrentState: function() {
            // We add dt so that we can uniquely identify this event state
            const dt = Date.now() - this.$store.state.sessionTime;
            const showInfo = this.$store.state.showInfo;
            let showName = null;
            let seasonName = null;
            let episodeName = null;
            if (showInfo) {
                if (typeof showInfo.name === "object") showName = showInfo.name.hz;
                else showName = showInfo.name;
                const [seasonIdx, episodeIdx] = findVideoInShowInfo(showInfo, this.$store.state.captionId);
                if (seasonIdx !== null) {
                    let seasonName = showInfo.seasons[seasonIdx].name;
                    if (! seasonName) {
                        seasonName = showInfo.seasons.length > 1 ? 'Season ' + (seasonIdx + 1) : null;
                    }

                    let episodeName = showInfo.seasons[seasonIdx].episodes[episodeIdx].name;
                    if (! episodeName) {
                        episodeName = showInfo.seasons[seasonIdx].length > 1 ? 'Episode ' + (episodeIdx + 1) : null;
                    }
                }
            }

            let captionIdx = this.currentCaptionIdx;
            if (Array.isArray(captionIdx)) {
                captionIdx = captionIdx[0];
            }
            return {
                data: this.data,
                translationIdx: this.translationIdx,
                hidden: this.hiddenStates,
                dt: dt,
                showName: showName,
                seasonName: seasonName,
                episodeName: episodeName,
                captionIdx: captionIdx,
            };
        },
        click: function(type, i = null) {
            if (this.waitingBeforeClosingMenu) {
                this.cancelCloseContextMenu = true;
            }
            if (type === 'translation') {
                if (this.hiddenStates[type] === true) {
                    if (this.hiddenAndNotPeeking[type] === false) {
                        const lastVal = this.showContextMenu[type];
                        this.resetShowContextMenu(this.wordData);
                        this.showContextMenu[type] = ! lastVal;
                    }
                    else {
                        this.$store.commit('setPeekState', {'type': type, 'i': i});
                        this.appendSessionLog([getEvent('peek', 'translation')]);
                    }
                }
                else {
                    const lastVal = this.showContextMenu[type];
                    this.resetShowContextMenu(this.wordData);
                    this.showContextMenu[type] = ! lastVal;
                }
                return;
            }

            if (this.wordData.pys[i] === null) return;

            if (this.hiddenStates[type][i] === true && ! this.purePeekStates[type][i]) {
                this.$store.commit('setPeekState', {'type': type, 'i': i});
                this.appendSessionLog([getEvent('peek', 'tr'), i]);
            }
            else {
                const lastVal = this.showContextMenu[type][i];
                this.resetShowContextMenu(this.wordData);
                this.showContextMenu[type][i] = ! lastVal;
            }
        },
        mouseleave: function(event, type, i = null) {
            if (
                type === 'translation' && this.showContextMenu[type] ||
                this.showContextMenu[type][i]
            ) {
                const self = this;
                const mouseOverListener = event.target.addEventListener('mouseover', function() {
                    self.cancelCloseContextMenu = true;
                }, { once: true });

                this.cancelCloseContextMenu = false;
                this.waitingBeforeClosingMenu = true;
                setTimeout(function() {
                    this.waitingBeforeClosingMenu = false;
                    event.target.removeEventListener('mouseover', mouseOverListener);
                    if (self.cancelCloseContextMenu) {
                        self.cancelCloseContextMenu = false;
                        return;
                    }
                    self.resetShowContextMenu(self.wordData);
                }, 500);
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
        isHiddenStoreOrLvlStates: function(type, hz, pys) {
            const key = getStateKey(type, hz, pys, null, null);
            return (
                getState(this.lvlStates, key, StateHidden, StateNone) === StateHidden ||
                getState(this.$store.state.states, key, StateHidden, StateNone) === StateHidden
            );
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
                for (var type of ['hz', 'py', 'tr']) {
                    const key = this.stateKey(type, i);
                    if (
                        getState(k, key, StateHidden, StateNone) == StateNone &&
                        (
                            getState(this.lvlStates, key, StateHidden, StateNone) == StateHidden ||
                            this.$store.state.options.hideLevels[type] === 7 || // all
                            ( // Any number + MW should be hidden if hide level is > 2
                                hz.match(/^[一二三四五六七八九十百千万个]+$/) &&
                                this.$store.state.options.hideLevels[type] > 2
                            )
                        )
                    ) {
                        console.log('LVLS: Marking', type, hz, pys, tr, 'as hidden');
                        applyState(d, k, type, hz, pys, tr, this.wordData.translation, StateHidden, StateHidden, true, true);
                        this.appendSessionLog([getEvent('hide_auto', type), i]);
                    }
                }
            }
        },
        applyPinyinComponents: function() {
            // If user hides ni3hao3, we should hide ni3 and hao3 separately, but not other way around.

            const d = this.$store.state.DICT;
            const k = this.$store.state.states;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.hz[i];
                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];

                const key = getStateKey('py', hz, pys, null, null);
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

                        console.log('applyPinyinComponents: ', 'py', hzSub, pysSub);
                        applyState(d, k, 'py', hzSub, pysSub, null, this.wordData.translation, StateHidden, StateHidden, false, true);
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

                const allHidden = {hz: true, tr: true, py: true};
                for (const [wordHz, wordPys] of words) {
                    for (const type of ['hz', 'tr', 'py']) {
                        allHidden[type] = allHidden[type] && this.isHiddenStoreOrLvlStates(type, wordHz, wordPys);
                    }
                }

                for (const type of ['hz', 'tr', 'py']) {
                    if (getState(k, this.stateKey(type, i), StateHidden, StateNone) === StateHidden) {
                        continue;
                    }

                    if (type === 'py' && !allHidden.tr) {
                        // Do nothing, we don't want to hide py unless tr is hidden first
                    }
                    else if (type === 'hz' && (!allHidden.tr || !allHidden.py)) {
                        // Do nothing, we don't want to hide hz unless both py and tr are also hidden
                    }
                    else if (allHidden[type]) {
                        console.log('applyCompoundWordsNotInDict', type, hz, pys);
                        applyState(d, k, type, hz, pys, null, null, StateHidden, StateHidden, false, true);
                        this.appendSessionLog([getEvent('hide_auto', type), i]);
                    }
                }
            }
        },
        applySimpleCompounds: function() {
            // Where there is a main component, and an additional "simple" character like 了
            // For example, 地上, 拿不着, 这样的, 不服气, 知道了, middle chars: 离不开, 想不到

            const simpleCharsPrePost = ['上', '下', '啊', '吗', '呗', '嘛', '呀', '啦', '吧', '呢', '哟', '喽', '来', '不'];
            const simpleCharsPre = ['有'];
            const simpleCharsMiddle = ['不'];
            const simpleCharsPost = ['地', '不着', '着', '了', '个', '点', '到', '儿', '里', '的', '得', '过', '子', '去', '好', '者'];

            const d = this.$store.state.DICT;
            const k = this.$store.state.states;
            if (d === null || k === null) return;

            for (let i = 0; i < this.wordData.hz.length; i++) {
                const hz = this.wordData.hz[i];
                if (hz.length < 2) continue;

                const pys = this.wordData.pys[i];
                const tr = this.wordData.tr[i];

                const allHidden = {hz: false, tr: false, py: false};
                for (const type of ['hz', 'py', 'tr']) {
                    if (getState(k, this.stateKey(type, i), StateHidden, StateNone) === StateHidden) {
                        continue;
                    }

                    for (const indices of [[[0, 1], [1, hz.length]], [[hz.length-1, hz.length], [0, hz.length-1]]]) {
                        const preIdx = indices[0];
                        const postIdx = indices[1];
                        let checkChars = [...simpleCharsPrePost];
                        if (preIdx[0] === 0) checkChars = checkChars.concat(simpleCharsPre);
                        else checkChars = checkChars.concat(simpleCharsPost);

                        if (checkChars.includes(hz.substring(preIdx[0], preIdx[1]))) {
                            const preHz = hz.substring(preIdx[0], preIdx[1]);
                            const postHz = hz.substring(postIdx[0], postIdx[1]);
                            const prePys = pys.slice(preIdx[0], preIdx[1]);
                            const postPys = pys.slice(postIdx[0], postIdx[1]);
                            allHidden[type] = allHidden[type] || (
                                this.isHiddenStoreOrLvlStates(type, preHz, prePys) &&
                                this.isHiddenStoreOrLvlStates(type, postHz, postPys)
                            );
                        }
                    }

                    for (const middleChar of simpleCharsMiddle) {
                        if (! hz.substring(1, hz.length-1).includes(middleChar)) continue;

                        const middleIdx = hz.indexOf(middleChar);
                        const prePostHz = hz.substring(0, middleIdx) + hz.substring(middleIdx + 1);
                        const prePostPys = pys.slice(0, middleIdx).concat(pys.slice(middleIdx + 1));
                        allHidden[type] = allHidden[type] || this.isHiddenStoreOrLvlStates(type, prePostHz, prePostPys);
                    }
                }

                for (const type of ['hz', 'py', 'tr']) {
                    if (type === 'py' && !allHidden.tr) {
                        // Do nothing, we don't want to hide py unless tr is hidden first
                    }
                    else if (type === 'hz' && (!allHidden.tr || !allHidden.py)) {
                        // Do nothing, we don't want to hide hz unless both py and tr are also hidden
                    }
                    else if (allHidden[type]) {
                        console.log('applySimpleCompounds', type, hz, pys);
                        applyState(d, k, type, hz, pys, null, null, StateHidden, StateHidden, false, true);
                        this.appendSessionLog([getEvent('hide_auto', type), i]);
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

/*
.captioncard.captioncardhidden.starred {
    border: 1px dashed darkorange;
    border-radius: 3px;
}
*/

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
    border-radius: 3px;
}

.centerrow .captioncardhidden.starred  {
    border: 1px dashed darkorange !important;
}

.cardcontent {
    position: relative;
}

.captioncard.peeking:not(.fulltranslation) .cardcontent {
    /*color: #32de84;*/
    color: gray;
}

.captioncard.peeking:hover .cardcontent {
    color: lightgray;
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

.captioncard:hover:not(.fulltranslation):not(.captioncardhidden) .starbadge {
    display: none !important;
}

.captioncardhidden .starbadge {
    display: none !important;
}

.captioncard .statsbadge {
    margin-top: -5px;
    margin-right: -5px;
}

.captioncard .starbadge {
    margin-top: -5px;
    margin-right: -10px;
}

</style>
