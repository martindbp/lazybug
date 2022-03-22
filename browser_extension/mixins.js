const mixin = {
    methods: {
        sm2tr(text) {
            if (this.$store.state.DICT === null) return null;
            if (this.$store.state.options.characterSet == 'sm') return text;

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
                    if (hideHz) applyState(d, states, 'hz', hz, null, null, null, StateHidden, StateHidden, false);
                    const entries = d[hz];
                    if (entries === undefined) continue;

                    for (let entry of entries) {
                        entry = dictArrayToDict(entry);
                        const pys = entry.pys;
                        if (hidePy) applyState(d, states, 'py', hz, pys, null, null, StateHidden, StateHidden, false);
                        if (hideTr) applyState(d, states, 'tr', hz, pys, null, null, StateHidden, StateHidden, false);
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

