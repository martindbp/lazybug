function combinations(options, accumulatorArray, currCombination = [], currIdx = 0) {
    if (currIdx === options.length) {
        accumulatorArray.push(currCombination);
        return;
    }

    for (const item of options[currIdx]) {
        //let newCombination = [...currCombination];
        let newCombination = currCombination.concat(item);
        combinations(options, accumulatorArray, newCombination, currIdx + 1);
    }
}

const mixin = {
    methods: {
        sm2tr(text, optionsOverride = true) {
            if (this.$store.state.DICT === null) return null;
            if (optionsOverride && this.$store.state.options.characterSet == 'sm') return text;

            let trText = '';
            let nextIdx = 0;
            while (nextIdx < text.length) {
                let foundStr = text.substring(nextIdx, nextIdx+1);
                for (var i = nextIdx+1; i < text.length; i++) {
                    const subStr = text.substring(nextIdx, i);
                    if (this.$store.state.DICT[foundStr] !== undefined) {
                        break;
                    }
                    foundStr = subStr;
                }
                let entries = this.$store.state.DICT[foundStr];
                if (entries !== undefined) {
                    trText += dictArrayToDict(entries[0]).hzTrad;
                }
                else {
                    trText += foundStr;
                }

                nextIdx += foundStr.length;
            }

            return trText;
        },
        appendSessionLog(data) {
            appendSessionLog(this.$store.state, data);
        },
        createSession() {
            createSession(this.$store.state);
        },
    },
    computed: {
        lvlStates: function() {
            if (this.$store.state.DICT === null || this.$store.state.HSK_WORDS === null) return {};
            const d = this.$store.state.DICT;
            const states = {};
            for (let lvl = 1; lvl <= 6; lvl++) {
                const hidePy = lvl <= this.$store.state.options.hideLevels.py;
                const hideHz = lvl <= this.$store.state.options.hideLevels.hz;
                const hideTr = lvl <= this.$store.state.options.hideLevels.tr;

                for (const hz of this.$store.state.HSK_WORDS[lvl-1]) {
                    if (hideHz) applyState(d, states, 'hz', hz, null, null, null, StateHidden, StateHidden, true, false);
                    let entries = d[hz];
                    let entryPys = [];
                    if (entries === undefined) {
                        // No entry, so pick all combinations of single char pys
                        const charPyOptions = [];
                        for (const c of hz) {
                            const charEntryPys = [];
                            for (let entry of d[c]) {
                                charEntryPys.push(dictArrayToDict(entry).pys)
                            }
                            charPyOptions.push(charEntryPys);
                        }
                        combinations(charPyOptions, entryPys);
                    }
                    else {
                        for (let entry of entries) {
                            entryPys.push(dictArrayToDict(entry).pys);
                        }
                    }

                    for (let pys of entryPys) {
                        if (hidePy) applyState(d, states, 'py', hz, pys, null, null, StateHidden, StateHidden, true, false);
                        if (hideTr) applyState(d, states, 'tr', hz, pys, null, null, StateHidden, StateHidden, true, false);
                    }
                }
            }
            return states;
        },
        videoWordStats: function() {
            if (this.$store.state.captionData === null) return {};
            const wordStats = {};
            for (let line of this.$store.state.captionData.lines) {
                line = captionArrayToDict(line, this.$store.state.captionData);
                for (let alignment of line.alignments) {
                    const hz = alignment[2];
                    const py = alignment[3].map((item) => item[0]).join('');
                    const key = `${hz}-${py}`;
                    if (wordStats[key] === undefined) {
                        wordStats[key] = 0;
                    }
                    wordStats[key] += 1;
                }
            }

            return wordStats;
        },
        purePeekStates: function() {
            const states = this.$store.state.peekStates;
            states['translation'] = states['translation'] && this.hiddenStates['translation'];
            for (var i = 0; i < this.wordData.hz.length; i++) {
                for (var type of ['hz', 'py', 'tr']) {
                    states[type][i] = states[type][i] && this.hiddenStates[type][i];
                }
            }
            return states;
        },
    },
};

